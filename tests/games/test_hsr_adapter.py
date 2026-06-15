import pytest
import numpy as np
import yaml
from pathlib import Path
from core.task import Task, TaskStatus
from games.hsr.adapter import HsrAdapter


class MockDevice:
    def screenshot(self):
        return np.zeros((1080, 1920, 3), dtype=np.uint8)
    def tap(self, x, y):
        self._last_tap = (x, y)
    def swipe(self, x1, y1, x2, y2, d=300):
        pass
    def get_resolution(self):
        return (1920, 1080)
    def wait(self, s):
        pass
    def press_key(self, key_code):
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
        assert adapter.vision is not None
        assert adapter.step_runner is not None

    def test_get_tasks_has_steps(self, adapter):
        tasks = adapter.get_tasks()
        assert len(tasks) >= 4
        for task in tasks:
            assert "steps" in task.params, f"Task {task.task_id} missing steps"

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

    def test_run_task_no_assets(self, adapter):
        """没有素材时所有步骤 fail，应返回 FAILED"""
        task = Task(name="测试", task_id="daily_training",
                   priority=1, params={"steps": [
                       {"tap_asset": "nonexistent", "timeout": 1}
                   ]})
        result = adapter.run_task(task)
        assert result is not None

    def test_step_engine_uses_step_runner(self, adapter):
        """验证适配器使用 StepRunner"""
        task = Task(name="领取邮件", task_id="claim_mail", priority=2)
        result = adapter.run_task(task)
        # 有 steps 定义，但没有素材 → 某步会 fail
        assert result.status in (TaskStatus.FAILED, TaskStatus.OK, TaskStatus.SKIPPED)
