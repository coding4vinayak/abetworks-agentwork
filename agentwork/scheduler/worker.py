"""Worker - long-running process that polls scheduler and executes due jobs."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from agentwork.scheduler.scheduler import Scheduler

logger = logging.getLogger(__name__)


class Worker:
    """Long-running worker daemon that executes scheduled jobs.

    Usage:
        scheduler = Scheduler()
        scheduler.add_job(my_func, IntervalTrigger(seconds=10))

        worker = Worker(scheduler)
        worker.start()  # Blocks - runs until stop() is called
    """

    def __init__(
        self,
        scheduler: Optional[Scheduler] = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.scheduler = scheduler or Scheduler()
        self.poll_interval = poll_interval
        self._running = False
        self._executed_count = 0

    @property
    def running(self) -> bool:
        """Check if the worker is running."""
        return self._running

    @property
    def executed_count(self) -> int:
        """Get the number of jobs executed by this worker."""
        return self._executed_count

    def start(self) -> None:
        """Start the worker loop (blocking). Call stop() from another thread to halt."""
        self._running = True
        self.scheduler.start()
        logger.info("Worker started, polling every %.1fs", self.poll_interval)

        while self._running:
            self._tick()
            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Stop the worker loop."""
        self._running = False
        self.scheduler.stop()
        logger.info("Worker stopped after executing %d jobs", self._executed_count)

    def _tick(self) -> None:
        """Execute one poll cycle."""
        due_jobs = self.scheduler.get_due_jobs()
        for job in due_jobs:
            try:
                job.func(*job.args, **job.kwargs)
                job.run_count += 1
                self._executed_count += 1
                logger.debug("Executed job '%s' (run #%d)", job.name, job.run_count)

                # Mark trigger as fired if it supports it
                if hasattr(job.trigger, "mark_fired"):
                    job.trigger.mark_fired()
            except Exception as e:
                job.last_error = str(e)
                logger.error("Job '%s' failed: %s", job.name, str(e))

    async def start_async(self) -> None:
        """Start the worker loop asynchronously."""
        self._running = True
        self.scheduler.start()
        logger.info("Async worker started, polling every %.1fs", self.poll_interval)

        while self._running:
            self._tick()
            await asyncio.sleep(self.poll_interval)

    def tick_once(self) -> int:
        """Execute a single tick (useful for testing). Returns number of jobs executed."""
        due_jobs = self.scheduler.get_due_jobs()
        count = 0
        for job in due_jobs:
            try:
                job.func(*job.args, **job.kwargs)
                job.run_count += 1
                self._executed_count += 1
                count += 1
                if hasattr(job.trigger, "mark_fired"):
                    job.trigger.mark_fired()
            except Exception as e:
                job.last_error = str(e)
                logger.error("Job '%s' failed: %s", job.name, str(e))
        return count
