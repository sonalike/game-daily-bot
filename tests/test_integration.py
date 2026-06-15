"""集成测试 — 验证完整流程"""
import pytest
import yaml
from pathlib import Path


class TestConfigIntegrity:
    """验证配置文件完整性"""

    def test_global_config_exists(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        assert config_path.exists(), "全局配置缺失"

    def test_global_config_valid(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert "device" in config
        assert "schedule" in config
        assert "execution" in config
        assert "games" in config

    def test_hsr_config_exists(self):
        config_path = Path(__file__).parent.parent / "games" / "hsr" / "config.yaml"
        assert config_path.exists(), "星穹铁道配置缺失"

    def test_hsr_config_valid(self):
        config_path = Path(__file__).parent.parent / "games" / "hsr" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert "game" in config
        assert "tasks" in config
        assert "claim_mail" in config["tasks"]


class TestCoreImports:
    """验证所有核心模块可导入"""

    def test_import_device(self):
        from core.device import Device, AdbDevice
        assert Device is not None
        assert AdbDevice is not None

    def test_import_vision(self):
        from core.vision import Vision
        assert Vision is not None

    def test_import_task(self):
        from core.task import Task, TaskResult, TaskStatus, GameAdapter
        assert Task is not None
        assert GameAdapter is not None

    def test_import_runner(self):
        from core.runner import TaskRunner
        assert TaskRunner is not None

    def test_import_scheduler(self):
        from core.scheduler import Scheduler
        assert Scheduler is not None

    def test_import_logger(self):
        from core.logger import GameLogger
        assert GameLogger is not None

    def test_import_hsr(self):
        from games.hsr.adapter import HsrAdapter
        assert HsrAdapter is not None
