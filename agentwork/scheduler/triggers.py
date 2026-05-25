"""Trigger types for job scheduling: cron, interval, once."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from croniter import croniter


class BaseTrigger(ABC):
    """Abstract base for trigger types."""

    @abstractmethod
    def next_fire_time(self, now: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate the next fire time from the given time."""
        ...

    @abstractmethod
    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Check if the trigger is due to fire."""
        ...


class CronTrigger(BaseTrigger):
    """Cron-expression based trigger.

    Usage:
        trigger = CronTrigger("*/5 * * * *")  # Every 5 minutes
        trigger = CronTrigger("0 9 * * MON")  # 9 AM every Monday
    """

    def __init__(self, expression: str) -> None:
        self.expression = expression
        # Validate expression
        croniter(expression)

    def next_fire_time(self, now: Optional[datetime] = None) -> Optional[datetime]:
        """Get the next fire time based on cron expression."""
        base_time = now or datetime.utcnow()
        cron = croniter(self.expression, base_time)
        return cron.get_next(datetime)

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Check if the cron trigger is due (within 1 second tolerance)."""
        current = now or datetime.utcnow()
        cron = croniter(self.expression, current - timedelta(seconds=1))
        next_time = cron.get_next(datetime)
        return abs((next_time - current).total_seconds()) < 1


class IntervalTrigger(BaseTrigger):
    """Fixed interval trigger.

    Usage:
        trigger = IntervalTrigger(seconds=30)  # Every 30 seconds
        trigger = IntervalTrigger(minutes=5)   # Every 5 minutes
    """

    def __init__(
        self,
        seconds: float = 0,
        minutes: float = 0,
        hours: float = 0,
        start_time: Optional[datetime] = None,
    ) -> None:
        self.interval = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        if self.interval.total_seconds() <= 0:
            raise ValueError("Interval must be positive")
        self._start_time = start_time or datetime.utcnow()
        self._last_fire: Optional[datetime] = None

    def next_fire_time(self, now: Optional[datetime] = None) -> Optional[datetime]:
        """Get the next fire time based on interval."""
        current = now or datetime.utcnow()
        if self._last_fire is None:
            return self._start_time + self.interval
        return self._last_fire + self.interval

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Check if the interval has elapsed."""
        current = now or datetime.utcnow()
        next_time = self.next_fire_time(current)
        if next_time is None:
            return False
        return current >= next_time

    def mark_fired(self, at: Optional[datetime] = None) -> None:
        """Mark the trigger as having fired."""
        self._last_fire = at or datetime.utcnow()


class OnceTrigger(BaseTrigger):
    """One-time trigger that fires at a specific time.

    Usage:
        trigger = OnceTrigger(run_at=datetime(2024, 1, 1, 12, 0))
    """

    def __init__(self, run_at: Optional[datetime] = None, delay_seconds: float = 0) -> None:
        if run_at:
            self.run_at = run_at
        else:
            self.run_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        self._fired = False

    def next_fire_time(self, now: Optional[datetime] = None) -> Optional[datetime]:
        """Get the fire time (or None if already fired)."""
        if self._fired:
            return None
        return self.run_at

    def is_due(self, now: Optional[datetime] = None) -> bool:
        """Check if the trigger time has passed."""
        if self._fired:
            return False
        current = now or datetime.utcnow()
        return current >= self.run_at

    def mark_fired(self) -> None:
        """Mark as fired so it won't fire again."""
        self._fired = True
