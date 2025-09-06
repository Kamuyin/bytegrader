import copy
import json
import os.path
from datetime import datetime, timezone

import nbformat
from tornado.httputil import HTTPFile

from bytegrader.repositories.submission import SubmissionRepository
from ..core.auth.decorators import permission_manager
from ..core.database.connection import DatabaseManager
from ..core.exceptions import DatabaseError
from ..core.models import AssignmentAsset
from ..core.models.base import new_uuid
from ..core.models.enum import CellType
from ..core.utils.lti import LTIClient
from ..preprocessors.factory import ProcessorFactory
from ..repositories.asset import AssignmentAssetRepository
from ..repositories.assignment import AssignmentRepository
from ..schemas.assignment import AssignmentCreateRequest, AssignmentListItemSchema, NotebookSchema, \
    AssignmentSubmissionSchema
from ..core.models.course import Assignment as AssignmentModel
from ..core.models.notebook import Cell, Notebook
from ..core.models.user import User


class AssignmentService:
    def __init__(
            self,
            repo: 'AssignmentRepository',
            submission_repo: 'SubmissionRepository',
            asset_repo: 'AssignmentAssetRepository',
            db_mgr: 'DatabaseManager',
            lti_client: 'LTIClient' = None
    ):
        self.repo = repo
        self.sub_repo = submission_repo
        self.asset_repo = asset_repo
        self.db_mgr = db_mgr
        self.lti_client = lti_client

    def create_assignment(
            self,
            req_model: AssignmentCreateRequest,
            course_id: str,
            notebooks: list[HTTPFile],
            assets: list[HTTPFile] = None
    ) -> AssignmentModel:
        existing = self.repo.get_by_course_and_name(course_id, req_model.name)
        if existing:
            raise ValueError(f"Assignment with label '{req_model.name}' already exists.")
        data = req_model.model_dump()

        assignment = AssignmentModel(
            id=new_uuid(),
            course_id=course_id,
            name=req_model.name,
            description=req_model.description,
            due_date=req_model.due_date,
            visible=req_model.visible,
            allow_resubmission=req_model.allow_resubmission,
            allow_late_submission=req_model.allow_late_submission,
            show_solutions=req_model.show_solutions,
            created_at=datetime.now().replace(tzinfo=timezone.utc)
        )

        notebook_models = []
        cell_models = []
        asset_models = []

        # Deconstruct notebooks
        for nb_idx, notebook in enumerate(notebooks):
            content = notebook.body.decode("utf-8")
            try:
                nb = nbformat.reads(content, nbformat.current_nbformat)
                nbformat.validate(nb)
            except Exception as e:
                raise ValueError(f"Invalid notebook file: {e}")

            if not nb.cells:
                raise ValueError("Notebook must contain at least one cell.")

            kernelspec = nb.get('metadata', {}).get('kernelspec', {})

            try:
                pipeline = ProcessorFactory.create_assignment_generation_pipeline()
                student_nb, _ = pipeline.process(copy.deepcopy(nb), {})
            except Exception as e:
                raise ValueError(f"Failed to process notebook: {e}")

            nb_model = Notebook(
                id=new_uuid(),
                assignment_id=assignment.id,
                name=notebook.filename,
                idx=nb_idx,
                kernelspec=json.dumps(kernelspec),
                created_at=datetime.now().replace(tzinfo=timezone.utc),
            )

            for cell_idx, nb_cell in enumerate(nb.cells):
                student_cell = student_nb['cells'][cell_idx] if cell_idx < len(student_nb['cells']) else None
                if hasattr(nb_cell, 'metadata'):
                    cell_meta = student_cell.metadata.copy()
                    cell_meta.pop('nbgrader', None)
                    nbgrader_meta = nb_cell.metadata.get('nbgrader', {})
                    cell_type = CellType.CODE if nb_cell.cell_type == 'code' else CellType.MARKDOWN
                    cell_src = nb_cell.source
                    cell_id = new_uuid()
                else:
                    cell_meta = {}
                    nbgrader_meta = {}
                    cell_type = CellType.CODE if nb_cell.cell_type == 'code' else CellType.MARKDOWN
                    cell_src = nb_cell.source
                    cell_id = new_uuid()

                is_grade = nbgrader_meta.get('grade', False)
                is_solution = nbgrader_meta.get('solution', False)
                is_locked = nbgrader_meta.get('locked', False)
                is_task = nbgrader_meta.get('task', False)
                max_score = nbgrader_meta.get('points', 0.0) if is_grade else 0.0

                cell_name = nbgrader_meta.get('name', None)

                if isinstance(cell_src, list):
                    cell_src = "".join(cell_src)
                else:
                    cell_src = cell_src or ""

                student_src = cell_src
                if student_cell:
                    if hasattr(student_cell, 'source'):
                        student_src_raw = student_cell.source
                    else:
                        student_src_raw = student_cell.get('source', "")

                    if isinstance(student_src_raw, list):
                        student_src = "".join(student_src_raw)
                    else:
                        student_src = student_src_raw or ""

                cell = Cell(
                    id=cell_id,
                    notebook_id=nb_model.id,
                    name=cell_name,
                    idx=cell_idx,
                    cell_type=cell_type,
                    source=cell_src,
                    source_student=student_src,
                    is_grade=is_grade,
                    is_solution=is_solution,
                    is_locked=is_locked,
                    is_task=is_task,
                    max_score=max_score,
                    created_at=datetime.now().replace(tzinfo=timezone.utc),
                    meta=json.dumps(cell_meta),
                )

                cell_models.append(cell)
            notebook_models.append(nb_model)

        if assets and self.db_mgr.config.database.asset_path:
            base_asset_path = self.db_mgr.config.database.asset_path

            for asset in assets:
                file_uuid = new_uuid()

                file_pth = os.path.join(base_asset_path, file_uuid)

                with open(file_pth, 'wb') as f:
                    f.write(asset.body)

                asset_model = AssignmentAsset(
                    id=file_uuid,
                    assignment_id=assignment.id,
                    path=asset.filename,
                    size=len(asset.body),
                    created_at=datetime.now().replace(tzinfo=timezone.utc),
                )

                asset_models.append(asset_model)

        if req_model.lti_sync:

            with self.db_mgr.get_session() as sess:
                course = sess.get(AssignmentModel.course.property.mapper.class_, course_id)
                if not course:
                    raise ValueError(f"Course with id '{course_id}' not found.")

            score_maximum = sum(cell.max_score for cell in cell_models if cell.is_grade)

            lti_assignment = self.lti_client.create_assignment(
                course.lti_id,
                assignment.name,
                score_maximum=score_maximum,
                tag=assignment.id,
            )
            assignment.lti_id = lti_assignment.id

        with self.db_mgr.get_session() as sess:
            sess.add(assignment)
            sess.add_all(notebook_models)
            sess.add_all(cell_models)
            sess.add_all(asset_models)

            sess.commit()

        return assignment

    def fetch_assignment(self, assignment: AssignmentModel, solution: bool = False):
        notebooks = []

        # Reconstruct assignment notebooks from database.
        for notebook in assignment.notebooks:
            nb = nbformat.v4.new_notebook()

            if notebook.kernelspec:
                try:
                    kernelspec = json.loads(notebook.kernelspec)
                    nb.metadata.kernelspec = kernelspec
                except (json.JSONDecodeError, TypeError):
                    pass

            sorted_cells = sorted(notebook.cells, key=lambda c: c.idx)

            nb.cells = []
            for cell in sorted_cells:
                src = cell.source if solution else cell.source_student
                
                if cell.cell_type == CellType.CODE:
                    nb_cell = nbformat.v4.new_code_cell(src)
                elif cell.cell_type == CellType.MARKDOWN:
                    nb_cell = nbformat.v4.new_markdown_cell(src)
                else:
                    nb_cell = nbformat.v4.new_code_cell(src)

                nbgrader_meta = {
                    'grade': cell.is_grade,
                    'solution': cell.is_solution,
                    'locked': cell.is_locked,
                    'task': cell.is_task,
                    'points': cell.max_score,
                    'grade_id': cell.name,
                }

                metadata = {}
                if cell.meta:
                    try:
                        metadata = json.loads(cell.meta) if isinstance(cell.meta, str) else cell.meta
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse metadata for cell {cell.id}, using empty metadata")
                        metadata = {}

                metadata['nbgrader'] = nbgrader_meta

                nb_cell.metadata = metadata
                nb_cell.id = cell.id
                nb.cells.append(nb_cell)

            notebooks.append((notebook.name, nb))

        assets = self.asset_repo.list_by_assignment(assignment.id)

        return notebooks, assets

    def list_assignments(self, course_id: str, user: User):
        assignments = self.repo.get_by_course(course_id)

        visible_assignments = []
        enrollment = next((e for e in user.enrollments if e.course_id == course_id), None)

        for assignment in assignments:
            ctx = {
                'assignment': assignment,
                'course': assignment.course,
                'enrollment': enrollment
            }

            if permission_manager.check(user, 'assignment:view', ctx):
                visible_assignments.append(assignment)

        ids = [a.id for a in visible_assignments]
        subs = self.sub_repo.list_for_user_and_assignments(user.id, ids)
        sub_map = {s.assignment_id: s for s in subs}

        res = []
        for a in visible_assignments:
            notebooks = [
                NotebookSchema(
                    id=nb.id,
                    name=nb.name,
                    idx=nb.idx,
                    max_score=nb.max_score
                )
                for nb in a.notebooks
            ]

            s = sub_map.get(a.id)
            sub = (
                AssignmentSubmissionSchema(
                    id=s.id,
                    submitted_at=s.submitted_at,
                    status=s.status,
                    is_late=s.is_late,
                    total_score=s.total_score,
                    auto_score=s.auto_score,
                    manual_score=s.manual_score,
                    needs_manual_grading=s.needs_manual_grading,
                    graded_at=s.graded_at,
                    graded_by=s.graded_by,
                )
                if s
                else None
            )

            item = AssignmentListItemSchema(
                id=a.id,
                name=a.name,
                description=a.description,
                due_date=a.due_date,
                visible=a.visible,
                created_at=a.created_at,
                allow_resubmission=a.allow_resubmission,
                notebooks=notebooks,
                submission=sub
            )
            res.append(item)

        return res

    def delete_assignment(self, assignment_id: str, course_id: str):
        existing = self.repo.get(assignment_id)
        if not existing:
            raise DatabaseError(f"Assignment with id '{assignment_id}' not found.")
        try:
            self.repo.delete(assignment_id)
        except Exception as e:
            raise DatabaseError(f"Assignment deletion failed: {e}")