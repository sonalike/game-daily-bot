"""崩坏：星穹铁道 游戏适配器"""
import yaml
from pathlib import Path
from core.task import Task, TaskResult, GameAdapter


HERE = Path(__file__).parent
ASSETS_DIR = HERE / "assets"


class HsrAdapter(GameAdapter):
    """星穹铁道适配器"""

    GAME_PACKAGE = "com.miHoYo.hkrpg"
    GAME_ACTIVITY = ".MainActivity"

    def __init__(self, device, config: dict):
        super().__init__(device, config)
        self.assets = ASSETS_DIR

    def launch_game(self):
        """通过 ADB 启动游戏"""
        # am start -n com.miHoYo.hkrpg/.MainActivity
        pass

    def get_tasks(self) -> list[Task]:
        """从配置生成任务列表"""
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
                params={k: v for k, v in cfg.items()
                        if k not in ("enabled", "priority", "description")}
            )
            tasks.append(task)

        return sorted(tasks, key=lambda t: t.priority)

    def run_task(self, task: Task) -> TaskResult:
        """执行单个任务（路由到具体方法）"""
        method_name = f"_do_{task.task_id}"
        method = getattr(self, method_name, None)

        if method is None:
            return TaskResult.skip(f"任务 {task.task_id} 未实现")

        return method(task)

    # ── Placeholder task methods ──

    def _do_signin(self, task: Task) -> TaskResult:
        return TaskResult.skip("签到逻辑待实现（需素材）")

    def _do_claim_mail(self, task: Task) -> TaskResult:
        return TaskResult.skip("邮件领取待实现（需素材）")

    def _do_dispatch(self, task: Task) -> TaskResult:
        return TaskResult.skip("派遣待实现（需素材）")

    def _do_spend_stamina(self, task: Task) -> TaskResult:
        return TaskResult.skip("清体力待实现（需素材）")

    def _do_sim_universe(self, task: Task) -> TaskResult:
        return TaskResult.skip("模拟宇宙待实现（需素材）")
