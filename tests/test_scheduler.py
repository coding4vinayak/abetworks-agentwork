"""Tests for the scheduler system."""

import time
from datetime import datetime, timedelta

import pytest

from agentwork import Scheduler, Worker
from agentwork.scheduler.triggers import CronTrigger, IntervalTrigger, OnceTrigger


class TestTriggers:
    def test_interval_trigger_is_due(self):
        trigger = IntervalTrigger(seconds=0.01, start_time=datetime.utcnow() - timedelta(seconds=1))
        assert trigger.is_due()

    def test_interval_trigger_not_due(self):
        trigger = IntervalTrigger(seconds=3600)
        # Just created, first fire is start_time + interval (1 hour from now)
        assert not trigger.is_due()

    def test_interval_trigger_mark_fired(self):
        trigger = IntervalTrigger(seconds=0.01, start_time=datetime.utcnow() - timedelta(seconds=1))
        assert trigger.is_due()
        trigger.mark_fired()
        # After marking fired, next fire is now + interval
        assert not trigger.is_due()

    def test_once_trigger(self):
        # Already past
        trigger = OnceTrigger(run_at=datetime.utcnow() - timedelta(seconds=1))
        assert trigger.is_due()
        trigger.mark_fired()
        assert not trigger.is_due()

    def test_once_trigger_not_due(self):
        trigger = OnceTrigger(run_at=datetime.utcnow() + timedelta(hours=1))
        assert not trigger.is_due()

    def test_cron_trigger_creation(self):
        trigger = CronTrigger("*/5 * * * *")
        assert trigger.expression == "*/5 * * * *"

    def test_cron_trigger_invalid(self):
        with pytest.raises(Exception):
            CronTrigger("invalid cron")

    def test_interval_trigger_invalid(self):
        with pytest.raises(ValueError):
            IntervalTrigger(seconds=0)


class TestScheduler:
    def test_add_job(self):
        scheduler = Scheduler()
        trigger = IntervalTrigger(seconds=60)
        job = scheduler.add_job(lambda: None, trigger, name="test_job")
        assert job.name == "test_job"
        assert len(scheduler.jobs) == 1

    def test_remove_job(self):
        scheduler = Scheduler()
        trigger = IntervalTrigger(seconds=60)
        job = scheduler.add_job(lambda: None, trigger)
        scheduler.remove_job(job.id)
        assert len(scheduler.jobs) == 0

    def test_get_due_jobs(self):
        scheduler = Scheduler()
        # This trigger is already due
        trigger = IntervalTrigger(
            seconds=0.01, start_time=datetime.utcnow() - timedelta(seconds=1)
        )
        scheduler.add_job(lambda: None, trigger, name="due_job")

        # This one is not due
        trigger2 = IntervalTrigger(seconds=3600)
        scheduler.add_job(lambda: None, trigger2, name="not_due")

        due = scheduler.get_due_jobs()
        assert len(due) == 1
        assert due[0].name == "due_job"

    def test_start_stop(self):
        scheduler = Scheduler()
        assert not scheduler.running
        scheduler.start()
        assert scheduler.running
        scheduler.stop()
        assert not scheduler.running


class TestWorker:
    def test_tick_once(self):
        results = []

        def job_func():
            results.append("executed")

        scheduler = Scheduler()
        trigger = IntervalTrigger(
            seconds=0.01, start_time=datetime.utcnow() - timedelta(seconds=1)
        )
        scheduler.add_job(job_func, trigger, name="test")

        worker = Worker(scheduler)
        scheduler.start()
        count = worker.tick_once()
        assert count == 1
        assert len(results) == 1
        assert worker.executed_count == 1

    def test_worker_handles_job_error(self):
        def bad_job():
            raise RuntimeError("job failed")

        scheduler = Scheduler()
        trigger = IntervalTrigger(
            seconds=0.01, start_time=datetime.utcnow() - timedelta(seconds=1)
        )
        job = scheduler.add_job(bad_job, trigger, name="bad")

        worker = Worker(scheduler)
        scheduler.start()
        # Should not raise
        worker.tick_once()
        assert job.last_error == "job failed"
