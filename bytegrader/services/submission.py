from datetime import datetime, timezone

import nbformat
import sqlalchemy
from tornado.httputil import HTTPFile

from bytegrader.autograde.service import AutogradingService
from bytegrader.core.models import Assignment, Submission, User, NotebookSubmission, CellSubmission
from bytegrader.core.models.base import new_uuid
from bytegrader.core.models.enum import SubmissionStatus
from bytegrader.repositories.submission import SubmissionRepository
from bytegrader.core.observability import capture_exception, set_span_attributes


class SubmissionService:
    def __init__(self, repo: 'SubmissionRepository', autograde_service: 'AutogradingService'):
        self.repo = repo
        self.autograde_service = autograde_service

    async def submit_assignment(self, assignment: 'Assignment', user: 'User',
                                notebooks: list[HTTPFile]) -> 'Submission':

        set_span_attributes(
            {
                "component": "submission_service",
                "submission.assignment_id": assignment.id,
                "submission.user_id": user.id,
                "submission.notebook_count": len(notebooks),
            }
        )

        # Archive any existing submissions for this assignment and user
        existing_submissions = self.repo.list_for_user_and_assignments(
            user_id=user.id, 
            assignment_ids=[assignment.id],
            include_archived=False
        )
        
        # Archive existing submissions
        with self.repo.db_manager.get_session() as session:
            for existing_submission in existing_submissions:
                session.query(Submission).filter(
                    Submission.id == existing_submission.id
                ).update({Submission.status: SubmissionStatus.ARCHIVED})
            session.commit()

        submission = Submission(
            id=new_uuid(),
            assignment_id=assignment.id,
            user_id=user.id,
            status=SubmissionStatus.SUBMITTED,
            submitted_at=datetime.now().replace(tzinfo=timezone.utc),
        )
        set_span_attributes({"submission.id": submission.id})

        """
        TODO: Asset submission? Additional field in the `assignment_assets` table as indicator whether that asset 
        should be submitted as well?
        """

        notebook_files = {nb.filename: nb for nb in notebooks}
        notebook_submissions = []
        cell_submissions = []

        for assignment_notebook in assignment.notebooks:
            if assignment_notebook.name not in notebook_files:
                continue
            notebook_file = notebook_files[assignment_notebook.name]

            # Notebook deconstruction
            try:
                body = notebook_file.body.decode('utf-8')
                nb = nbformat.reads(body, nbformat.current_nbformat)
                nbformat.validate(nb)
            except Exception as e:
                raise ValueError(f"Invalid notebook file {assignment_notebook.name}: {e}")

            notebook_submission = NotebookSubmission(
                id=new_uuid(),
                submission_id=submission.id,
                notebook_id=assignment_notebook.id,
            )
            notebook_submissions.append(notebook_submission)

            cell_map = {cell.id: cell for cell in assignment_notebook.cells}

            for nb_cell in nb.cells:
                cell_id = getattr(nb_cell, 'id', None)
                if not cell_id or cell_id not in cell_map:
                    # raise ValueError(f"Cell ID {cell_id} not found in notebook {assignment_notebook.filename}")
                    continue

                orig_cell = cell_map[cell_id]

                is_grade = orig_cell.is_grade
                is_solution = orig_cell.is_solution
                is_locked = orig_cell.is_locked

                if not ((is_grade and not is_solution) or (is_locked and not is_grade and not is_solution)):
                    cell_src = nb_cell.source
                    if isinstance(cell_src, list):
                        cell_src = "".join(cell_src)

                    cell_submission = CellSubmission(
                        id=new_uuid(),
                        notebook_submission_id=notebook_submission.id,
                        cell_id=cell_id,
                        submitted_source=cell_src,
                    )
                    cell_submissions.append(cell_submission)

        # ! Delete/Archive previous submissions
        with self.repo.db_manager.get_session() as session:
            try:
                session.add(submission)
                session.add_all(notebook_submissions)
                session.add_all(cell_submissions)
                session.commit()

                submission_id = submission.id
                loaded_submission = session.query(Submission).filter(
                    Submission.id == submission_id
                ).options(
                    sqlalchemy.orm.joinedload(Submission.assignment),
                    sqlalchemy.orm.joinedload(Submission.notebook_submissions).joinedload(
                        NotebookSubmission.grades
                    ),
                    sqlalchemy.orm.joinedload(Submission.notebook_submissions).joinedload(
                        NotebookSubmission.cell_submissions
                    )
                ).one()

                session.expunge_all()

                # Submit for autograding
                if self.autograde_service.running:
                    try:
                        job_id = await self.autograde_service.submit_for_grading(assignment, loaded_submission)
                        set_span_attributes(
                            {
                                "submission.autograde.job_id": job_id,
                            }
                        )
                    except Exception as e:
                        session.rollback()
                        capture_exception(
                            e,
                            tags={
                                "component": "submission_service",
                                "stage": "submit_for_grading",
                            },
                            extra={
                                "assignment_id": assignment.id,
                                "submission_id": loaded_submission.id,
                                "user_id": user.id,
                            }
                        )
                        raise ValueError(f"Failed to submit for autograding: {e}")

                return loaded_submission

            except Exception as e:
                session.rollback()
                capture_exception(
                    e,
                    tags={
                        "component": "submission_service",
                        "stage": "persist_submission",
                    },
                    extra={
                        "assignment_id": assignment.id,
                        "user_id": user.id,
                    }
                )
                raise ValueError(f"Failed to submit assignment: {e}")
