"""崩坏：星穹铁道 游戏适配器 — YAML 步骤驱动"""
from pathlib import Path
from core.task import Task, TaskResult, GameAdapter
from core.step_runner import StepRunner


HERE = Path(__file__).parent
ASSETS_DIR = HERE / "assets"


class HsrAdapter(GameAdapter):
    """星穹铁道适配器"""

    def __init__(self, device, config: dict):
        super().__init__(device, config)
        from core.vision import Vision
        self.vision = Vision(str(ASSETS_DIR))
        self.step_runner = StepRunner(device, self.vision, str(ASSETS_DIR))

    def launch_game(self):
        """PC客户端 — 由用户手动启动"""
        pass

    def get_tasks(self) -> list[Task]:
        """从配置生成任务列表 (含 YAML 步骤)"""
        tasks_config = self.config.get("tasks", {})
        tasks = []
        for task_id, cfg in tasks_config.items():
            if not cfg.get("enabled", True):
                continue
            task = Task(
                name=cfg.get("description", task_id),
                task_id=task_id,
                priority=cfg.get("priority", 99),
                enabled=cfg.get("enabled", True),
                params={
                    "steps": cfg.get("steps", []),
                    # 额外参数传给 StepRunner
                    **{k: v for k, v in cfg.items()
                       if k not in ("enabled", "priority", "description", "steps")}
                }
            )
            tasks.append(task)
        return sorted(tasks, key=lambda t: t.priority)

    def run_task(self, task: Task) -> TaskResult:
        """使用 StepRunner 执行 YAML 步骤"""
        self.step_runner.logger = None  # logger handled by TaskRunner
        return self.step_runner.execute(task)
