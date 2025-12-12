import asyncio
import importlib
import logging
from typing import List

from apscheduler.job import Job

from bytegrader.autograde.executors.mock import MockExecutor
from bytegrader.autograde.queue import JobQueue
from bytegrader.autograde.worker import AutogradingWorker, AutogradingJob
from bytegrader.config.config import BYTEGraderConfig
from bytegrader.core.database.connection import DatabaseManager
from bytegrader.core.models import Submission, Assignment
from bytegrader.core.models.enum import SubmissionStatus
from bytegrader.core.utils.lti import LTIClient
from bytegrader.core.observability import capture_exception, set_span_attributes


class AutogradingService:

    def __init__(self, config: BYTEGraderConfig, db_mgr: DatabaseManager, lti_client: LTIClient =None):
        self.config = config
        self.db_mgr = db_mgr
        self.lti_client = lti_client
        self.log = logging.getLogger(__name__)

        self.queue = JobQueue(max_size=128)

        self.workers: List[AutogradingWorker] = []
        executor_class_path = self.config.autograde.executor_class
        if not executor_class_path:
            raise ValueError("No executor_class specified in AutogradeConfig")

        try:
            module_name, class_name = executor_class_path.rsplit('.', 1)
            module = importlib.import_module(module_name)
            executor_class = getattr(module, class_name)
        except Exception as e:
            self.log.error(f"Failed to load executor class '{executor_class_path}': {e}")
            capture_exception(
                e,
                tags={
                    "component": "autograde_service",
                    "stage": "load_executor",
                },
                extra={
                    "executor_path": executor_class_path,
                }
            )
            raise

        for i in range(self.config.autograde.workers):
            executor = executor_class(parent=self.config)
            worker = AutogradingWorker(f"worker-{i}", executor)
            self.workers.append(worker)

        self.running = False
        self.worker_tasks = []

        set_span_attributes(
            {
                "component": "autograde_service",
                "autograde.worker.count": len(self.workers),
                "autograde.executor_class": executor_class_path,
            }
        )

    async def start(self):
        if self.running:
            return

        self.running = True
        set_span_attributes({"component": "autograde_service", "autograde.service.running": True})

        self.worker_tasks = [asyncio.create_task(self._worker_loop(worker)) for worker in self.workers]

    async def stop(self):
        if not self.running:
            return

        self.running = False
        self.log.info("Stopping autograding service")
        set_span_attributes({"component": "autograde_service", "autograde.service.running": False})

        for task in self.worker_tasks:
            task.cancel()

        try:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        self.worker_tasks = []

    async def _worker_loop(self, worker: AutogradingWorker):
        self.log.info(f"Worker {worker.id} started")

        try:
            while self.running:
                job = None
                try:
                    job = await self.queue.get_job()

                    set_span_attributes(
                        {
                            "component": "autograde_service",
                            "autograde.worker.id": worker.id,
                            "autograde.job.id": job.id,
                        }
                    )

                    await worker.process_job(job)

                    await self._save_results(job)

                    self.queue.task_done()

                except asyncio.CancelledError:
                    self.log.info(f"Worker {worker.id} cancelled")
                    break
                except Exception as e:
                    self.log.error(f"Worker {worker.id} encountered an error: {e}")
                    job_id = job.id if job else None
                    capture_exception(
                        e,
                        tags={
                            "component": "autograde_worker_loop",
                            "worker_id": worker.id,
                        },
                        extra={
                            "job_id": job_id,
                        }
                    )
                    self.queue.task_done()

        finally:
            self.log.info(f"Worker {worker.id} stopped")

    async def _save_results(self, job: AutogradingJob):
        try:
            set_span_attributes(
                {
                    "component": "autograde_service",
                    "autograde.job.id": job.id,
                    "autograde.job.submission_id": job.submission_id,
                    "autograde.assignment.id": job.assignment.id,
                }
            )
            with self.db_mgr.get_session() as sess:
                grades = []
                for notebook_id, cells in job.grades.items():
                    for cell_id, grade in cells.items():
                        grades.append(grade)

                sess.add_all(grades)

                submission = sess.query(Submission).filter(
                    Submission.id == job.submission_id
                ).one()
                submission.status = SubmissionStatus.GRADED

                sess.commit()

                self.log.info(f"Submission {submission.id} added to database")
                if job.assignment.lti_id and self.lti_client:
                    submission = sess.get(Submission, submission.id)
                    all_grades = []
                    for notebook_sub in submission.notebook_submissions:
                        for grade in notebook_sub.grades:
                            all_grades.append(grade)

                    achieved = sum(g.final_score for g in all_grades)

                    max_possible = 0.0
                    for nb in job.assignment.notebooks:
                        for cell in nb.cells:
                            if cell.is_grade:
                                max_possible += cell.max_score

                    if max_possible <= 0:
                        self.log.warning("Assignment has no gradable points. Sending score 0.0 to LTI")
                        scaled_score = 0.0
                    else:
                        remote_max = getattr(job.assignment, 'score_maximum', None) or max_possible
                        proportion = min(max(achieved / max_possible, 0.0), 1.0)
                        scaled_score = proportion * remote_max

                    self.log.debug(
                        f"Submitting {job.assignment.lti_id} to LTI (achieved={achieved}, max={max_possible}, sent={scaled_score})"
                    )
                    try:
                        user = submission.user
                        self.lti_client.submit_score(
                            job.assignment.course.lti_id,
                            job.assignment.lti_id,
                            user.lms_user_id,
                            scaled_score,
                            score_max=max_possible if max_possible > 0 else None
                        )
                        set_span_attributes(
                            {
                                "component": "autograde_service",
                                "autograde.lti.assignment_id": job.assignment.lti_id,
                                "autograde.lti.user_id": user.lms_user_id,
                                "autograde.lti.score_sent": scaled_score,
                            }
                        )
                    except Exception as lti_err:
                        self.log.error(f"LTI submission failed for job {job.id}: {lti_err}")
                        capture_exception(
                            lti_err,
                            tags={
                                "component": "autograde_service",
                                "stage": "lti_submit_score",
                            },
                            extra={
                                "job_id": job.id,
                                "assignment_id": job.assignment.id,
                                "submission_id": submission.id,
                            }
                        )

                self.log.debug(f"Saved results for job {job.id} with {len(grades)} grades")
        except Exception as e:
            self.log.error(f"Failed to save results for job {job.id}: {e}")
            capture_exception(
                e,
                tags={
                    "component": "autograde_service",
                    "stage": "save_results",
                },
                extra={
                    "job_id": getattr(job, 'id', None),
                    "submission_id": getattr(job, 'submission_id', None),
                }
            )
            raise

    async def submit_for_grading(self, assignment: Assignment, submission: Submission) -> str:
        if not self.running:
            exc = RuntimeError("Autograding service is not running")
            capture_exception(
                exc,
                tags={
                    "component": "autograde_service",
                    "stage": "submit_for_grading",
                },
                extra={
                    "assignment_id": assignment.id,
                    "submission_id": submission.id,
                }
            )
            raise exc

        self.log.debug(f"Submitting {assignment} with submission {submission.id}")
        set_span_attributes(
            {
                "component": "autograde_service",
                "autograde.assignment.id": assignment.id,
                "autograde.submission.id": submission.id,
            }
        )
        job = AutogradingJob(submission.id, assignment, submission)
        await self.queue.add_job(job)

        return job.id
