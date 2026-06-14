"""Tests for core.scheduler"""
import pytest
from unittest.mock import MagicMock
from core.scheduler import Scheduler, ScheduleConfig


class TestScheduleConfig:
    def test_default_config(self):
        cfg = ScheduleConfig()
        assert cfg.daily_time == "06:00"
        assert cfg.enabled is True

    def test_custom_config(self):
        cfg = ScheduleConfig(daily_time="08:00", enabled=False)
        assert cfg.daily_time == "08:00"
        assert cfg.enabled is False


class TestScheduler:
    @pytest.fixture
    def scheduler(self):
        return Scheduler()

    def test_init(self, scheduler):
        assert scheduler._running is False

    def test_add_game(self, scheduler):
        mock_runner = MagicMock()
        scheduler.add_game("hsr", mock_runner)
        assert "hsr" in scheduler._games

    def test_remove_game(self, scheduler):
        mock_runner = MagicMock()
        scheduler.add_game("hsr", mock_runner)
        scheduler.remove_game("hsr")
        assert "hsr" not in scheduler._games

    def test_get_games(self, scheduler):
        scheduler.add_game("hsr", MagicMock())
        scheduler.add_game("yh", MagicMock())
        names = scheduler.get_game_names()
        assert set(names) == {"hsr", "yh"}

    def test_run_all_now(self, scheduler):
        mock_runner = MagicMock()
        mock_runner.run_all.return_value = []
        scheduler.add_game("hsr", mock_runner)
        results = scheduler.run_all_now()
        assert "hsr" in results
        mock_runner.run_all.assert_called_once()

    def test_run_single_game(self, scheduler):
        mock_hsr = MagicMock()
        mock_hsr.run_all.return_value = [MagicMock()]
        mock_yh = MagicMock()
        scheduler.add_game("hsr", mock_hsr)
        scheduler.add_game("yh", mock_yh)
        results = scheduler.run_game_now("hsr")
        assert len(results) == 1
        mock_hsr.run_all.assert_called_once()
        mock_yh.run_all.assert_not_called()

    def test_run_nonexistent_game(self, scheduler):
        with pytest.raises(KeyError):
            scheduler.run_game_now("nonexistent")
