import enum
import json
import logging
from datetime import datetime

import nbformat.v4

from bytegrader.autograde.executors.base import BaseExecutor
from bytegrader.core.models import Assignment, Submission, Notebook, NotebookSubmission
from bytegrader.core.models.base import new_uuid
from bytegrader.core.models.enum import CellType
from bytegrader.core.observability import (
    capture_exception,
    capture_message,
    set_span_attributes,
)


class WorkerStatus(enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


class AutogradingJob:

    def __init__(self, submission_id: str, assignment: Assignment, submission: Submission):
        self.id = f"job-{submission_id}"
        self.submission_id = submission_id
        self.assignment: Assignment = assignment
        self.submission: Submission = submission
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.completed = False
        self.error = None
        self.grades = {}

    def get_or_create_grade(self, notebook_submission_id: str, cell_id: str):
        if notebook_submission_id not in self.grades:
            self.grades[notebook_submission_id] = {}

        if cell_id not in self.grades[notebook_submission_id]:
            from bytegrader.core.models import Grade
            self.grades[notebook_submission_id][cell_id] = Grade(
                id=new_uuid(),
                notebook_submission_id=notebook_submission_id,
                cell_id=cell_id,
                auto_score=0.0,
                needs_manual_grading=True
            )

        return self.grades[notebook_submission_id][cell_id]


class AutogradingWorker:

    def __init__(self, worker_id: str, executor):
        self.id = worker_id
        self.executor: BaseExecutor = executor
        self.status = WorkerStatus.IDLE
        self.current_job = None
        self.log = logging.getLogger(f"AutogradingWorker-{worker_id}")

    async def process_job(self, job: AutogradingJob):
        self.status = WorkerStatus.BUSY
        self.current_job = job
        job.started_at = datetime.now()
        self.log.info(f"Processing job {job.id} for submission {job.submission_id}")
        set_span_attributes(
            {
                "component": "autograde_worker",
                "autograde.worker.id": self.id,
                "autograde.job.id": job.id,
                "autograde.submission.id": job.submission_id,
                "autograde.assignment.id": job.assignment.id,
            }
        )

        try:
            notebook_submissions_map = {ns.notebook_id: ns for ns in job.submission.notebook_submissions}

            cell_submissions_map = {}
            for ns in job.submission.notebook_submissions:
                for cs in ns.cell_submissions:
                    cell_submissions_map[cs.cell_id] = cs

            for notebook in job.assignment.notebooks:
                notebook_sub = notebook_submissions_map.get(notebook.id)
                if not notebook_sub:
                    continue

                nb = nbformat.v4.new_notebook()

                if notebook.kernelspec:
                    try:
                        kernelspec = json.loads(notebook.kernelspec)
                        nb.metadata.kernelspec = kernelspec
                    except (json.JSONDecoder, TypeError):
                        pass

                sorted_cells = sorted(notebook.cells, key=lambda c: c.idx)

                nb.cells = []
                for cell in sorted_cells:
                    if cell.is_solution:
                        cell_sub = cell_submissions_map.get(cell.id)
                        src = cell_sub.submitted_source if cell_sub else cell.source_student
                    else:
                        src = cell.source

                    if cell.cell_type == CellType.CODE:
                        nb_cell = nbformat.v4.new_code_cell(source=src)
                    else:
                        nb_cell = nbformat.v4.new_markdown_cell(source=src)

                    metadata = {}
                    if cell.meta:
                        try:
                            metadata = json.loads(cell.meta) if isinstance(cell.meta, str) else cell.meta
                        except (json.JSONDecoder, TypeError):
                            metadata = {}

                    nb_cell.metadata = metadata
                    nb_cell.id = cell.id
                    nb.cells.append(nb_cell)

                #grade_cells = [cell for cell in notebook.cells if cell.is_grade]
                #cell_ids = [cell.id for cell in grade_cells]

                results = await self.executor.execute_notebook(nb, [cell.id for cell in notebook.cells])
                for cell_id, result in results.items():
                    orig_cell = next((c for c in notebook.cells if c.id == cell_id), None)
                    if not orig_cell:
                        continue

                    grade = job.get_or_create_grade(notebook_sub.id, cell_id)

                    if result['success']:
                        grade.auto_score = orig_cell.max_score
                        grade.execution_error = None
                    else:
                        grade.auto_score = 0.0
                        if isinstance(result['error'], dict):
                            grade.execution_error = result['error'].get('traceback', 'Unknown error')
                        else:
                            grade.execution_error = result['error'] or 'Unknown error'
                        capture_message(
                            "Autograde cell execution failed",
                            level="warning",
                            tags={
                                "component": "autograde_worker",
                                "worker_id": self.id,
                                "assignment_id": job.assignment.id,
                                "notebook_id": notebook.id,
                                "cell_id": cell_id,
                            },
                            extra={
                                "submission_id": job.submission_id,
                                "error": grade.execution_error,
                            }
                        )

                    grade.needs_manual_grading = False

            job.completed = True
            job.completed_at = datetime.now()
            self.log.info(f"Completed job {job.id} for submission {job.submission_id}")
            set_span_attributes(
                {
                    "component": "autograde_worker",
                    "autograde.job.id": job.id,
                    "autograde.job.completed": True,
                    "autograde.job.completed_at": job.completed_at.isoformat(),
                }
            )

            return job
        except Exception as e:
            self.log.error(f"Error processing job {job.id}: {e}")
            self.status = WorkerStatus.ERROR
            job.error = str(e)
            capture_exception(
                e,
                tags={
                    "component": "autograde_worker",
                    "worker_id": self.id,
                },
                extra={
                    "job_id": job.id,
                    "submission_id": job.submission_id,
                    "assignment_id": job.assignment.id,
                }
            )
            raise
        finally:
            self.status = WorkerStatus.IDLE
            self.current_job = None
