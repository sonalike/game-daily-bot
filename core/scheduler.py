"""调度器 — 定时/间隔/手动执行游戏任务"""
from dataclasses import dataclass
from core.task import TaskResult


@dataclass
class ScheduleConfig:
    daily_time: str = "06:00"
    enabled: bool = True
    interval_minutes: int = 0  # 0 = disabled


class Scheduler:
    """任务调度器 — 管理多款游戏的执行"""

    def __init__(self):
        self._games: dict[str, object] = {}
        self._running = False

    def add_game(self, name: str, runner) -> None:
        self._games[name] = runner

    def remove_game(self, name: str) -> None:
        self._games.pop(name, None)

    def get_game_names(self) -> list[str]:
        return list(self._games.keys())

    def run_all_now(self) -> dict[str, list[TaskResult]]:
        self._running = True
        all_results = {}
        for name, runner in self._games.items():
            try:
                results = runner.run_all()
                all_results[name] = results
            except Exception as e:
                all_results[name] = []
        self._running = False
        return all_results

    def run_game_now(self, name: str) -> list[TaskResult]:
        if name not in self._games:
            raise KeyError(f"未注册的游戏: {name}")
        return self._games[name].run_all()

    @property
    def is_running(self) -> bool:
        return self._running
