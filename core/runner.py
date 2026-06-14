"""任务执行引擎 — 状态机 + 重试 + 超时保护"""
import time
import random
from core.task import Task, TaskResult, TaskStatus, GameAdapter


class TaskRunner:
    """任务执行器 — 按优先级顺序执行游戏任务"""

    def __init__(self, adapter: GameAdapter, device,
                 step_timeout: int = 30, max_retries: int = 3,
                 game_timeout: int = 1800, logger=None):
        self.adapter = adapter
        self.device = device
        self.step_timeout = step_timeout
        self.max_retries = max_retries
        self.game_timeout = game_timeout

        if logger is None:
            from core.logger import GameLogger
            logger = GameLogger(adapter.__class__.__name__)
        self.logger = logger

    def _get_enabled_tasks(self) -> list[Task]:
        """获取启用的任务列表（按优先级排序）"""
        tasks = [t for t in self.adapter.get_tasks() if t.enabled]
        return sorted(tasks, key=lambda t: t.priority)

    def _human_delay(self, min_ms: int = 200, max_ms: int = 800):
        """随机延迟，模拟人类操作"""
        delay = random.uniform(min_ms, max_ms) / 1000.0
        self.device.wait(delay)

    def _run_single_task(self, task: Task) -> TaskResult:
        """执行单个任务（含重试逻辑）"""
        self.logger.info(f"开始执行: {task.name}")

        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                self.logger.info(f"重试 {attempt}/{self.max_retries}: {task.name}")

            try:
                result = self.adapter.run_task(task)
                if result.status == TaskStatus.OK:
                    self.logger.info(f"OK {task.name} 完成")
                    return result
                elif result.status == TaskStatus.SKIPPED:
                    self.logger.info(f"SKIP {task.name} 跳过: {result.message}")
                    return result
                else:
                    self.logger.warning(f"FAIL {task.name} 失败 (尝试 {attempt}): {result.message}")
            except Exception as e:
                self.logger.error(f"FAIL {task.name} 异常: {e}")

        self.logger.error(f"FAIL {task.name} 失败，已达最大重试次数")
        return TaskResult.fail(f"重试 {self.max_retries} 次后仍失败")

    def run_all(self) -> list[TaskResult]:
        """执行所有启用的任务"""
        tasks = self._get_enabled_tasks()
        self.logger.info(f"共 {len(tasks)} 个任务待执行")

        results = []
        start_time = time.time()

        for task in tasks:
            if time.time() - start_time > self.game_timeout:
                self.logger.error(f"全局超时 ({self.game_timeout}s)，跳过剩余任务")
                results.append(TaskResult.skip(f"全局超时: {task.name}"))
                continue

            self._human_delay()
            result = self._run_single_task(task)
            results.append(result)

        elapsed = time.time() - start_time
        ok_count = sum(1 for r in results if r.status == TaskStatus.OK)
        self.logger.info(f"完成: {ok_count}/{len(tasks)}, 耗时 {elapsed:.0f}s")
        return results
