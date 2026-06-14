"""游戏日常助手 - 入口点

用法:
    python main.py              # 启动桌面启动器
    python main.py --no-gui     # CLI 模式（直接执行所有任务）
    python main.py --game hsr   # 执行指定游戏
"""
import sys
import os
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="游戏日常助手 - 国内网游日常任务自动执行程序"
    )
    parser.add_argument("--no-gui", action="store_true", help="CLI 模式（无 GUI）")
    parser.add_argument("--game", type=str, help="指定游戏名称")
    return parser.parse_args()


def run_cli(args):
    """CLI 模式 — 无 GUI 直接执行"""
    import yaml
    from core.device import AdbDevice
    from core.scheduler import Scheduler
    from games.hsr.adapter import HsrAdapter
    from core.runner import TaskRunner

    print(" 游戏日常助手 (CLI 模式)")

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Connect device
    device_cfg = config["device"]
    device = AdbDevice(host=device_cfg["adb_host"], port=device_cfg["adb_port"])
    try:
        connected = device.connect()
        if connected:
            print("  设备已连接")
        else:
            print("  警告: 设备连接失败（模拟器未运行？）")
    except FileNotFoundError:
        print("  警告: ADB 未找到（请安装 ADB 或检查 PATH 环境变量）")
    except Exception as e:
        print(f"  警告: 设备连接异常: {e}")

    # Create scheduler
    scheduler = Scheduler()
    exec_cfg = config["execution"]

    for game_cfg in config.get("games", []):
        if not game_cfg.get("enabled", True):
            continue
        name = game_cfg["name"]

        game_config_path = game_cfg["config"]
        if not os.path.exists(game_config_path):
            print(f"  {name}: 配置文件不存在 ({game_config_path})，跳过")
            continue
        with open(game_config_path, 'r', encoding='utf-8') as f:
            game_config = yaml.safe_load(f)

        # Route to correct adapter
        if "星穹铁道" in name:
            adapter = HsrAdapter(device, game_config)
        else:
            print(f"  {name}: 适配器未实现，跳过")
            continue

        runner = TaskRunner(
            adapter, device,
            step_timeout=exec_cfg["step_timeout"],
            max_retries=exec_cfg["max_retries"],
            game_timeout=exec_cfg["game_timeout"]
        )
        scheduler.add_game(name, runner)
        print(f"  {name} 已注册")

    # Execute
    if args.game:
        results = {args.game: scheduler.run_game_now(args.game)}
    else:
        results = scheduler.run_all_now()

    # Output results
    for name, task_results in results.items():
        ok = sum(1 for r in task_results if r.status.value == "ok")
        failed = sum(1 for r in task_results if r.status.value == "failed")
        skipped = sum(1 for r in task_results if r.status.value == "skipped")
        print(f"\n  {name}:  OK {ok}  FAIL {failed}  SKIP {skipped}")

    print("\n  完成")


def run_gui():
    """GUI 模式 — 启动桌面启动器"""
    from launcher.main import main
    main()


if __name__ == '__main__':
    args = parse_args()
    if args.no_gui:
        run_cli(args)
    else:
        run_gui()
