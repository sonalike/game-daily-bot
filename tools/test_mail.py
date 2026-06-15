"""Quick test — use config-driven task runner for any HSR task"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from core.win32_device import Win32Device
from core.runner import TaskRunner
from core.task import Task
from games.hsr.adapter import HsrAdapter


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="claim_mail", help="Task ID to run (from config.yaml)")
    ap.add_argument("--window", default="星穹铁道", help="Window title substring")
    args = ap.parse_args()

    print("=" * 50)
    print(f"  星穹铁道 — 测试: {args.task}")
    print("=" * 50)

    # 1. 连接游戏窗口
    print(f"\n[1] 连接窗口 '{args.window}'...")
    device = Win32Device(window_title=args.window)
    if not device.hwnd:
        print("  ❌ 未找到游戏窗口")
        return
    w, h = device.get_resolution()
    print(f"  ✅ [{w}x{h}]")

    # 2. 加载配置
    with open("games/hsr/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 3. 创建适配器和 Runner
    adapter = HsrAdapter(device, config)
    runner = TaskRunner(adapter, device, max_retries=1)

    # 4. 找到对应任务
    task = None
    for t in adapter.get_tasks():
        if t.task_id == args.task:
            task = t
            break

    if task is None:
        print(f"  ❌ 未找到任务 '{args.task}'")
        available = [t.task_id for t in adapter.get_tasks()]
        print(f"  可用: {available}")
        return

    # 5. 执行
    print(f"\n[2] 执行: {task.name}")
    print(f"    步骤数: {len(task.params.get('steps', []))}")
    print("-" * 50)

    result = runner._run_single_task(task)

    print("-" * 50)
    status_map = {"ok": "✅ 成功", "failed": "❌ 失败", "skipped": "⏭️ 跳过"}
    print(f"\n结果: {status_map.get(result.status.value, result.status.value)}")
    print(f"详情: {result.message}")


if __name__ == "__main__":
    main()
