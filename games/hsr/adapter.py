"""崩坏：星穹铁道 游戏适配器"""
from pathlib import Path
import random
import time
from core.task import Task, TaskResult, GameAdapter


HERE = Path(__file__).parent
ASSETS_DIR = HERE / "assets"


class HsrAdapter(GameAdapter):
    """星穹铁道适配器 — PC 客户端版"""

    def __init__(self, device, config: dict):
        super().__init__(device, config)
        self.assets = ASSETS_DIR
        # 每个适配器持有自己的 Vision 实例
        from core.vision import Vision
        self.vision = Vision(str(self.assets))

    # ── 工具方法 ──

    def _asset(self, name: str) -> str:
        """获取素材完整路径"""
        return str(self.assets / f"{name}.png")

    def _find(self, name: str, timeout: float = 5):
        """在当前画面中查找素材，返回中心坐标"""
        try:
            asset_path = self._asset(name)
            if not Path(asset_path).exists():
                return None
            screenshot = self.device.screenshot()
            pos = self.vision.find(asset_path, screenshot)
            if pos is None and timeout > 0:
                pos = self.vision.wait_for(
                    lambda: self.device.screenshot(),
                    asset_path, timeout=timeout
                )
            return pos
        except (FileNotFoundError, OSError):
            return None

    def _tap_asset(self, name: str, timeout: float = 5, jitter: int = 5):
        """找到素材并点击（带随机偏移防检测）"""
        pos = self._find(name, timeout)
        if pos is None:
            return False
        x, y = pos
        # 加随机偏移，模拟人类点击不精确
        x += random.randint(-jitter, jitter)
        y += random.randint(-jitter, jitter)
        self.device.tap(x, y)
        return True

    def _wait_then_find(self, name: str, wait: float = 1.0, timeout: float = 5):
        """等待一段时间后查找素材"""
        time.sleep(wait)
        return self._find(name, timeout)

    def _human_pause(self, min_s: float = 0.3, max_s: float = 0.8):
        """随机停顿"""
        time.sleep(random.uniform(min_s, max_s))

    def launch_game(self):
        """启动游戏（PC客户端需手动启动，这里做窗口前置）"""
        # Win32Device 的 bring_to_foreground 已处理
        pass

    def get_tasks(self) -> list[Task]:
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
        method_name = f"_do_{task.task_id}"
        method = getattr(self, method_name, None)
        if method is None:
            return TaskResult.skip(f"任务 {task.task_id} 未实现")
        return method(task)

    # ══════════════════════════════════════════════════
    #  任务实现
    # ══════════════════════════════════════════════════

    def _do_signin(self, task: Task) -> TaskResult:
        """每日签到 — 单步：点击签到入口 → 点击领取 → 确认完成"""
        # Step 1: 点击签到入口
        if not self._tap_asset("signin_entry", timeout=5):
            return TaskResult.fail("找不到签到入口")
        self._human_pause()

        # Step 2: 点击领取按钮
        if not self._tap_asset("signin_claim", timeout=3):
            # 可能已经签过了
            if self._find("signin_done"):
                return TaskResult.skip("今日已签到")
            return TaskResult.fail("签到领取失败")
        self._human_pause()

        # Step 3: 验证签到完成
        if self._find("signin_done", timeout=3):
            return TaskResult.ok("签到完成")
        return TaskResult.ok("签到完成（未确认标识）")

    # ══════════════════════════════════════════════════
    #  多步骤示例：领取邮件（4步）
    # ══════════════════════════════════════════════════

    def _do_claim_mail(self, task: Task) -> TaskResult:
        """
        领取邮件 — 多步骤演示

        流程:
            主界面
            └→ [Step 1] 点击邮件入口 (mail_entry)
                └→ [Step 2] 等待邮件界面加载 (mail_claim_all 出现)
                    └→ [Step 3] 点击一键领取 (mail_claim_all)
                        └→ [Step 4] 确认领取成功（回到主界面 or mail_empty）

        每步失败时记录原因并返回 FAILED，Runner 自动重试。
        """
        self._human_pause()

        # ── Step 1: 从主界面点击邮件入口 ──
        # 先确保在主界面（查找主界面特征元素）
        # 如果找不到 mail_entry，可能是：
        #   a. 不在主界面 — 按返回键回退
        #   b. 素材未采集 — 日志会明确提示

        if not self._tap_asset("mail_entry", timeout=5):
            # 尝试按 Esc 回主界面再试
            self.device.press_key(0x1B)  # Esc key
            self._human_pause(1.0, 1.5)
            if not self._tap_asset("mail_entry", timeout=3):
                return TaskResult.fail("Step 1 失败: 找不到邮件入口 (mail_entry)")

        self._human_pause(0.5, 1.0)

        # ── Step 2: 等待邮件界面加载 ──
        # 特征：一键领取按钮 (mail_claim_all) 出现
        claim_btn = self._find("mail_claim_all", timeout=5)
        if claim_btn is None:
            # 可能没有未读邮件 → 直接跳过
            return TaskResult.skip("无可领取的邮件")

        self._human_pause(0.3, 0.6)

        # ── Step 3: 点击一键领取 ──
        x, y = claim_btn
        x += random.randint(-4, 4)  # jitter
        y += random.randint(-4, 4)
        self.device.tap(x, y)

        self._human_pause(0.5, 1.0)

        # ── Step 4: 验证领取成功 ──
        # 领取后：按钮消失 or 出现空邮件标识 or 领取完成提示
        if self._find("mail_claim_all", timeout=2):
            # 按钮还在 → 可能还有邮件没领完
            return TaskResult.ok("邮件已领取（可能还有剩余）")

        # 按钮消失了 → 领完了 ✅
        return TaskResult.ok("邮件领取完成")

    # ══════════════════════════════════════════════════

    def _do_dispatch(self, task: Task) -> TaskResult:
        """派遣收菜 — 多步骤"""
        # Step 1: 进入派遣
        if not self._tap_asset("dispatch_entry", timeout=5):
            return TaskResult.fail("找不到派遣入口")
        self._human_pause()

        # Step 2: 一键收取
        if self._tap_asset("dispatch_claim", timeout=3):
            self._human_pause()
            # Step 3: 一键再派遣
            if self._tap_asset("dispatch_redispatch", timeout=3):
                self._human_pause()
                # Step 4: 确认
                if self._tap_asset("dispatch_confirm", timeout=3):
                    return TaskResult.ok("派遣收菜+再派遣完成")
                return TaskResult.ok("已收取，再派遣确认失败")
            return TaskResult.ok("已收取（无可再派遣）")
        return TaskResult.skip("无已完成派遣")

    def _do_spend_stamina(self, task: Task) -> TaskResult:
        """清体力 — 循环步骤"""
        target = task.params.get("target", "auto")
        max_runs = int(task.params.get("max_runs", 99))

        runs = 0
        while runs < max_runs:
            # Step 1: 进入副本
            if not self._tap_asset("stamina_entry", timeout=3):
                if runs == 0:
                    return TaskResult.fail("找不到体力副本入口")
                break  # 没入口了 = 没体力了

            self._human_pause(0.5, 1.0)

            # Step 2: 开启自动战斗
            self._tap_asset("stamina_auto", timeout=2)

            # Step 3: 开始挑战
            if not self._tap_asset("stamina_start", timeout=3):
                return TaskResult.fail("无法开始挑战")

            # Step 4: 等待战斗完成
            self._human_pause(2.0, 5.0)
            done = self._find("stamina_complete", timeout=120)
            if done is None:
                return TaskResult.fail("战斗超时（未检测到完成标识）")

            # Step 5: 点击完成
            self.device.tap(done[0] + random.randint(-5, 5),
                           done[1] + random.randint(-5, 5))
            self._human_pause(0.5, 1.0)

            runs += 1
            # 检查是否还能继续
            if self._find("stamina_use_item"):
                use_items = task.params.get("use_items", True)
                if use_items:
                    self._tap_asset("stamina_use_item", timeout=2)
                    self._human_pause()
                else:
                    break

        return TaskResult.ok(f"体力清空完成 ({runs} 次)")

    def _do_sim_universe(self, task: Task) -> TaskResult:
        return TaskResult.skip("模拟宇宙待实现（需素材）")
