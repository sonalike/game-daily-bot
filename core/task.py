"""任务系统 — 数据结构 + GameAdapter 基类"""
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, Optional


class TaskStatus(Enum):
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    status: TaskStatus
    message: str = ""
    detail: Any = None

    @classmethod
    def ok(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.OK, message=message)

    @classmethod
    def fail(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.FAILED, message=message)

    @classmethod
    def skip(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.SKIPPED, message=message)


@dataclass
class Task:
    name: str
    task_id: str
    priority: int = 99
    enabled: bool = True
    params: dict = field(default_factory=dict)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)


class GameAdapter(ABC):
    """游戏适配器基类"""

    def __init__(self, device, config: dict):
        self.device = device
        self.config = config

    @abstractmethod
    def launch_game(self):
        """启动游戏到主界面"""
        ...

    @abstractmethod
    def get_tasks(self) -> list[Task]:
        """返回该游戏的所有任务列表（按优先级排序）"""
        ...

    @abstractmethod
    def run_task(self, task: Task) -> TaskResult:
        """执行单个任务"""
        ...
