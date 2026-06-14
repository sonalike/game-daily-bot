import pytest
from unittest.mock import MagicMock
from core.task import Task, TaskResult, TaskStatus, GameAdapter
from core.runner import TaskRunner


class MockDevice:
    def screenshot(self): return None
    def tap(self, x, y): pass
    def swipe(self, x1, y1, x2, y2, d=300): pass
    def get_resolution(self): return (1920, 1080)
    def wait(self, s): pass


class MockAdapter(GameAdapter):
    def launch_game(self):
        self._launched = True
    def get_tasks(self):
        return [
            Task(name="签到", task_id="s1", priority=1),
            Task(name="清体力", task_id="s2", priority=2),
            Task(name="模拟宇宙", task_id="s3", priority=3, enabled=False),
        ]
    def run_task(self, task):
        if task.task_id == "s1":
            return TaskResult.ok("签到完成")
        elif task.task_id == "s2":
            return TaskResult.fail("体力不足")
        return TaskResult.skip("跳过")


class TestTaskRunner:
    @pytest.fixture
    def runner(self):
        device = MockDevice()
        adapter = MockAdapter(device, {})
        return TaskRunner(adapter, device, step_timeout=30, max_retries=2)

    def test_runner_init(self, runner):
        assert runner.adapter is not None
        assert runner.max_retries == 2

    def test_get_enabled_tasks(self, runner):
        tasks = runner._get_enabled_tasks()
        assert len(tasks) == 2
        assert tasks[0].task_id == "s1"
        assert tasks[1].task_id == "s2"

    def test_run_single_task_ok(self, runner):
        task = Task(name="签到", task_id="s1")
        result = runner._run_single_task(task)
        assert result.status == TaskStatus.OK

    def test_run_all_tasks(self, runner):
        results = runner.run_all()
        assert len(results) == 2
        assert results[0].status == TaskStatus.OK
        assert results[1].status == TaskStatus.FAILED

    def test_retry_on_failure(self):
        call_count = [0]

        class FlakyAdapter(MockAdapter):
            def run_task(self, task):
                call_count[0] += 1
                if call_count[0] < 3:
                    return TaskResult.fail(f"attempt {call_count[0]} failed")
                return TaskResult.ok("3rd time succeeded")

        adapter = FlakyAdapter(MockDevice(), {})
        runner = TaskRunner(adapter, MockDevice(), max_retries=3)
        results = runner.run_all()
        assert results[0].status == TaskStatus.OK
