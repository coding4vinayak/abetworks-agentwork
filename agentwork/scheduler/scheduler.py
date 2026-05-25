"""Scheduler - manages job registration and scheduling."""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

from agentwork.scheduler.triggers import BaseTrigger

logger = logging.getLogger(__name__)


class Job:
    """A scheduled job."""

    def __init__(
        self,
        func: Callable[..., Any],
        trigger: BaseTrigger,
        name: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.name = name or (func.__name__ if hasattr(func, "__name__") else self.id)
        self.func = func
        self.trigger = trigger
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.enabled = True
        self.run_count = 0
        self.last_error: Optional[str] = None

    def is_due(self) -> bool:
        """Check if this job is due to execute."""
        return self.enabled and self.trigger.is_due()


class Scheduler:
    """Job scheduler supporting cron, interval, and one-time triggers.

    Usage:
        scheduler = Scheduler()
        scheduler.add_job(my_func, CronTrigger("*/5 * * * *"))
        scheduler.add_job(cleanup, IntervalTrigger(minutes=30))
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, Job] = {}
        self._running = False

    @property
    def jobs(self) -> List[Job]:
        """List all registered jobs."""
        return list(self._jobs.values())

    @property
    def running(self) -> bool:
        """Check if the scheduler is running."""
        return self._running

    def add_job(
        self,
        func: Callable[..., Any],
        trigger: BaseTrigger,
        name: Optional[str] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
    ) -> Job:
        """Register a job with a trigger."""
        job = Job(func=func, trigger=trigger, name=name, args=args, kwargs=kwargs)
        self._jobs[job.id] = job
        logger.info("Registered job '%s' (id=%s)", job.name, job.id)
        return job

    def remove_job(self, job_id: str) -> Optional[Job]:
        """Remove a job by ID."""
        return self._jobs.pop(job_id, None)

    def get_due_jobs(self) -> List[Job]:
        """Get all jobs that are currently due to execute."""
        return [job for job in self._jobs.values() if job.is_due()]

    def start(self) -> None:
        """Mark the scheduler as running."""
        self._running = True
        logger.info("Scheduler started with %d jobs", len(self._jobs))

    def stop(self) -> None:
        """Mark the scheduler as stopped."""
        self._running = False
        logger.info("Scheduler stopped")

    def clear(self) -> None:
        """Remove all jobs."""
        self._jobs.clear()
