"""Quick test — 单独测试星穹铁道邮件领取任务"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from core.win32_device import Win32Device
from core.runner import TaskRunner
from core.task import Task
from games.hsr.adapter import HsrAdapter


def main():
    print("=" * 50)
    print("  星穹铁道 — 邮件领取测试")
    print("=" * 50)

    # 1. 连接游戏窗口
    print("\n[1] 连接游戏窗口...")
    device = Win32Device(window_title="星穹铁道")
    if not device.hwnd:
        print("  ❌ 未找到游戏窗口，请确认星穹铁道已启动")
        return
    w, h = device.get_resolution()
    print(f"  ✅ 已连接 [{w}x{h}]")

    # 2. 加载配置
    with open("games/hsr/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 3. 创建适配器
    adapter = HsrAdapter(device, config)

    # 4. 创建 Runner（单次尝试，不重试）
    runner = TaskRunner(adapter, device, max_retries=1)

    # 5. 执行邮件任务
    task = Task(name="领取邮件", task_id="claim_mail", priority=1)
    print(f"\n[2] 执行任务: {task.name}")
    print("-" * 50)

    result = runner._run_single_task(task)

    print("-" * 50)
    status_map = {"ok": "✅ 成功", "failed": "❌ 失败", "skipped": "⏭️ 跳过"}
    print(f"\n结果: {status_map.get(result.status.value, result.status.value)}")
    print(f"详情: {result.message}")


if __name__ == "__main__":
    main()
