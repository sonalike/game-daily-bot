import pytest
import yaml
from pathlib import Path
from core.task import Task
from games.hsr.adapter import HsrAdapter


class MockDevice:
    def screenshot(self):
        return None

    def tap(self, x, y):
        pass

    def swipe(self, x1, y1, x2, y2, d=300):
        pass

    def get_resolution(self):
        return (1920, 1080)

    def wait(self, s):
        pass


class TestHsrAdapter:
    @pytest.fixture
    def config(self):
        config_path = Path(__file__).parent.parent.parent / "games" / "hsr" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def adapter(self, config):
        device = MockDevice()
        return HsrAdapter(device, config)

    def test_adapter_init(self, adapter):
        assert adapter is not None

    def test_get_tasks(self, adapter):
        tasks = adapter.get_tasks()
        assert len(tasks) >= 4
        task_ids = {t.task_id for t in tasks}
        assert "signin" in task_ids
        assert "dispatch" in task_ids
        assert "spend_stamina" in task_ids

    def test_tasks_sorted_by_priority(self, adapter):
        tasks = adapter.get_tasks()
        priorities = [t.priority for t in tasks]
        assert priorities == sorted(priorities)

    def test_disabled_task_not_in_list(self, adapter):
        tasks = adapter.get_tasks()
        task_ids = {t.task_id for t in tasks}
        assert "sim_universe" not in task_ids

    def test_launch_game(self, adapter):
        adapter.launch_game()

    def test_run_task_skip_for_unimplemented(self, adapter):
        task = Task(name="签到", task_id="signin", priority=1)
        result = adapter.run_task(task)
        assert result is not None
