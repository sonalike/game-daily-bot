"""YAML 驱动的任务步骤执行器 — 无需写 Python 即可定义游戏操作流程

配置文件格式 (games/<game>/config.yaml):

    tasks:
      claim_mail:
        enabled: true
        priority: 2
        description: "领取邮件"
        steps:
          - tap_asset: mail_icon          # 点击邮件图标
            timeout: 5
          - wait_asset: mail_claim_all    # 等待界面加载
            timeout: 5
          - tap_asset: mail_claim_all     # 点一键领取
            timeout: 3
            optional: true                # 找不到则跳过（可能无邮件）
          - wait: 1.5
          - check: mail_empty
            on_not_found: ok              # 领完了 → 成功
            on_found: ok                  # 还有 → 也成功

支持的步骤类型:

    tap_asset: name      找图并点击 (timeout, optional, jitter)
    wait_asset: name     等待图片出现 (timeout)
    wait_gone: name      等待图片消失 (timeout)
    wait: seconds        等待指定秒数
    press_esc            按 Esc 返回
    press_key: code      按指定键 (如 press_key: 13 表示 Enter)
    check: name          检查图片是否存在，分支跳转
                         (on_found / on_not_found: ok|skip|fail|continue|back)
"""
import time
import random
import numpy as np
from pathlib import Path
from core.task import Task, TaskResult


class StepRunner:
    """执行 YAML 定义的任务步骤序列"""

    def __init__(self, device, vision, assets_dir: str, logger=None):
        self.device = device
        self.vision = vision
        self.assets_dir = Path(assets_dir)
        self.logger = logger

    def _asset_path(self, name: str) -> str:
        return str(self.assets_dir / f"{name}.png")

    def _find(self, name: str, timeout: float = 5):
        """查找素材，返回坐标或 None"""
        path = self._asset_path(name)
        if not Path(path).exists():
            return None
        try:
            screenshot = self.device.screenshot()
            pos = self.vision.find(path, screenshot)
            if pos is None and timeout > 0:
                pos = self.vision.wait_for(
                    lambda: self.device.screenshot(),
                    path, timeout=timeout, interval=0.3
                )
            return pos
        except Exception:
            return None

    def _human_pause(self, a=0.3, b=0.7):
        time.sleep(random.uniform(a, b))

    def execute(self, task: Task) -> TaskResult:
        """执行一个任务的步骤序列"""
        steps = task.params.get("steps", [])
        if not steps:
            return TaskResult.fail("任务未定义步骤")

        self._log(f"开始: {task.name} ({len(steps)} 步)")

        for i, step in enumerate(steps):
            action, args = self._parse_step(step)
            self._log(f"  步骤 {i+1}/{len(steps)}: {action} {args}")

            result = self._run_step(action, args)

            if result == "ok":
                return TaskResult.ok(f"{task.name} 完成")
            elif result == "skip":
                return TaskResult.skip(f"{task.name}: {args.get('reason', '跳过')}")
            elif result == "fail":
                return TaskResult.fail(f"步骤 {i+1} 失败: {action}")
            elif result == "back":
                # 回退一步
                i = max(0, i - 2)
            # "continue" — 继续下一步

        return TaskResult.ok(f"{task.name} 完成")

    def _parse_step(self, step: dict) -> tuple[str, dict]:
        """解析步骤字典 → (action_name, args)"""
        action_map = [
            "tap_asset", "wait_asset", "wait_gone", "wait",
            "press_esc", "press_key", "check",
        ]
        for action in action_map:
            if action in step:
                value = step[action]
                args = {"value": value}

                for key in ["timeout", "optional", "jitter",
                           "on_found", "on_not_found", "reason",
                           "seconds"]:
                    if key in step:
                        args[key] = step[key]

                return action, args
        return "unknown", {"raw": step}

    def _run_step(self, action: str, args: dict) -> str:
        """执行单个步骤，返回 'continue'|'ok'|'skip'|'fail'|'back'"""

        # ── tap_asset ──
        if action == "tap_asset":
            name = args["value"]
            timeout = args.get("timeout", 5)
            optional = args.get("optional", False)
            jitter = args.get("jitter", 5)

            pos = self._find(name, timeout)
            if pos:
                x = pos[0] + random.randint(-jitter, jitter)
                y = pos[1] + random.randint(-jitter, jitter)
                self.device.tap(x, y)
                self._human_pause()
                return "continue"
            elif optional:
                return "continue"
            else:
                return "fail"

        # ── wait_asset ──
        elif action == "wait_asset":
            name = args["value"]
            timeout = args.get("timeout", 10)
            pos = self._find(name, timeout)
            if pos is None:
                return "fail"
            self._human_pause()
            return "continue"

        # ── wait_gone ──
        elif action == "wait_gone":
            name = args["value"]
            timeout = args.get("timeout", 30)
            path = self._asset_path(name)
            gone = self.vision.wait_until_gone(
                lambda: self.device.screenshot(),
                path, timeout=timeout
            )
            return "continue" if gone else "fail"

        # ── wait ──
        elif action == "wait":
            seconds = args.get("seconds", args.get("value", 1))
            if isinstance(seconds, dict):
                seconds = 1
            time.sleep(float(seconds))
            return "continue"

        # ── press_esc ──
        elif action == "press_esc":
            self.device.press_key(0x1B)  # VK_ESCAPE
            self._human_pause(0.5, 1.0)
            return "continue"

        # ── press_key ──
        elif action == "press_key":
            code = args.get("value", 13)
            if isinstance(code, str):
                code = int(code)
            self.device.press_key(code)
            self._human_pause()
            return "continue"

        # ── check ──
        elif action == "check":
            name = args["value"]
            pos = self._find(name, timeout=2)
            if pos is not None:
                branch = args.get("on_found", "continue")
            else:
                branch = args.get("on_not_found", "continue")
            return branch

        return "fail"

    def _log(self, msg: str):
        if self.logger:
            self.logger.info(msg)
