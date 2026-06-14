import pytest
import os
import tempfile
from core.logger import GameLogger


class TestGameLogger:
    @pytest.fixture
    def log_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_init_creates_game_logger(self, log_dir):
        logger = GameLogger("崩坏：星穹铁道", log_dir)
        assert logger.game_name == "崩坏：星穹铁道"
        logger.close()

    def test_log_info_writes_file(self, log_dir):
        logger = GameLogger("test_game", log_dir)
        logger.info("签到完成")
        logger.close()
        log_file = os.path.join(log_dir, "test_game.log")
        assert os.path.exists(log_file)
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "签到完成" in content

    def test_log_error(self, log_dir):
        logger = GameLogger("test_game", log_dir)
        logger.error("连接失败")
        logger.close()
        log_file = os.path.join(log_dir, "test_game.log")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "ERROR" in content
        assert "连接失败" in content
