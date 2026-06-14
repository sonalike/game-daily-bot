import pytest
from core.task import Task, TaskResult, TaskStatus, GameAdapter


class TestTask:
    def test_task_creation(self):
        t = Task(name="签到", task_id="signin", priority=1)
        assert t.name == "签到"
        assert t.task_id == "signin"
        assert t.priority == 1
        assert t.enabled is True

    def test_task_disabled(self):
        t = Task(name="模拟宇宙", task_id="simu", enabled=False)
        assert t.enabled is False

    def test_task_params(self):
        t = Task(name="清体力", task_id="stamina", params={"target": "auto", "count": 5})
        assert t.params["target"] == "auto"
        assert t.params["count"] == 5

    def test_task_equality(self):
        t1 = Task(name="A", task_id="a")
        t2 = Task(name="A", task_id="a")
        assert t1 == t2

    def test_task_sort_by_priority(self):
        tasks = [
            Task(name="C", task_id="c", priority=3),
            Task(name="A", task_id="a", priority=1),
            Task(name="B", task_id="b", priority=2),
        ]
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        assert [t.task_id for t in sorted_tasks] == ["a", "b", "c"]


class TestTaskResult:
    def test_success_result(self):
        r = TaskResult.ok("签到完成")
        assert r.status == TaskStatus.OK
        assert r.message == "签到完成"

    def test_fail_result(self):
        r = TaskResult.fail("找不到签到按钮")
        assert r.status == TaskStatus.FAILED
        assert r.message == "找不到签到按钮"

    def test_skip_result(self):
        r = TaskResult.skip("今日已完成")
        assert r.status == TaskStatus.SKIPPED


class TestGameAdapter:
    def test_abstract_class(self):
        """GameAdapter is abstract"""
        with pytest.raises(TypeError):
            GameAdapter(None, {})

    class FakeAdapter(GameAdapter):
        def launch_game(self):
            self._launched = True
        def get_tasks(self):
            return [Task(name="test", task_id="t1")]
        def run_task(self, task):
            return TaskResult.ok("done")

    def test_concrete_adapter(self):
        adapter = self.FakeAdapter(None, {})
        adapter.launch_game()
        assert adapter._launched is True
        tasks = adapter.get_tasks()
        assert len(tasks) == 1
        result = adapter.run_task(tasks[0])
        assert result.status == TaskStatus.OK
