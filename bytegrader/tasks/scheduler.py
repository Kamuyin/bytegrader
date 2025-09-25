import asyncio
import functools
import logging
from typing import Any, Callable
from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from ..config.config import BYTEGraderConfig
from ..core.observability import capture_exception, set_span_attributes


class TaskScheduler:
    def __init__(self, config: BYTEGraderConfig):
        self.config = config
        self.log = logging.getLogger(__name__)
        self.scheduler = None
        self._initialize_scheduler()

    def _initialize_scheduler(self) -> None:
        jobstores = {'default': MemoryJobStore()}
        self.scheduler = TornadoScheduler(jobstores=jobstores)
        self.log.info("Task scheduler initialized")

    def start(self) -> None:
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            self.log.info("Task scheduler started")

    def shutdown(self) -> None:
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            self.log.info("Task scheduler stopped")

    def _wrap_job(self, func: Callable, job_id: str) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any):
                try:
                    set_span_attributes(
                        {
                            "component": "task_scheduler",
                            "scheduler.job_id": job_id,
                        }
                    )
                    return await func(*args, **kwargs)
                except Exception as exc:
                    capture_exception(
                        exc,
                        tags={
                            "component": "task_scheduler",
                            "scheduler_job_id": job_id,
                        },
                        extra={
                            "job_id": job_id,
                        }
                    )
                    raise

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any):
            try:
                set_span_attributes(
                    {
                        "component": "task_scheduler",
                        "scheduler.job_id": job_id,
                    }
                )
                return func(*args, **kwargs)
            except Exception as exc:
                capture_exception(
                    exc,
                    tags={
                        "component": "task_scheduler",
                        "scheduler_job_id": job_id,
                    },
                    extra={
                        "job_id": job_id,
                    }
                )
                raise

        return sync_wrapper

    def add_job(self, func: Callable,
                job_id: str,
                interval: str = "5m",
                replace_existing: bool = True,
                **kwargs: Any) -> None:
        if not self.scheduler:
            self.log.warning("Scheduler not initialized. Cannot add job.")
            return

        interval_value = int(''.join(filter(str.isdigit, interval)))
        interval_unit = ''.join(filter(str.isalpha, interval))

        trigger_args = {}
        if interval_unit == 'm':
            trigger_args['minutes'] = interval_value
        elif interval_unit == 'h':
            trigger_args['hours'] = interval_value
        elif interval_unit == 'd':
            trigger_args['days'] = interval_value
        else:
            trigger_args['minutes'] = 5

        self.scheduler.add_job(
            func=self._wrap_job(func, job_id),
            trigger='interval',
            id=job_id,
            replace_existing=replace_existing,
            max_instances=1,
            **trigger_args,
            **kwargs
        )
        set_span_attributes(
            {
                "component": "task_scheduler",
                "scheduler.job_id": job_id,
                "scheduler.interval": interval,
            }
        )
        self.log.debug(f"Added job '{job_id}' with interval {interval}")
