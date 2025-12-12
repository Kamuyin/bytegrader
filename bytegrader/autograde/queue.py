import logging
from asyncio import Queue

from bytegrader.autograde.worker import AutogradingJob


class JobQueue:

    def __init__(self, max_size: int = 100):
        self.queue = Queue(maxsize=max_size)
        self.log = logging.getLogger("JobQueue")

    async def add_job(self, job: AutogradingJob):
        await self.queue.put(job)
        self.log.debug(f"Added job {job}. Queue size: {self.queue.qsize()}")

    async def get_job(self) -> AutogradingJob:
        job = await self.queue.get()
        self.log.debug(f"Retrieved job {job}. Queue size: {self.queue.qsize()}")
        return job

    def task_done(self):
        self.queue.task_done()
        self.log.debug(f"Job completed. Queue size: {self.queue.qsize()}")

    async def wait_empty(self):
        await self.queue.join()
        self.log.debug("All jobs in the queue have been processed.")