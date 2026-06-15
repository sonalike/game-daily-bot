"""素材采集工具 — 截取游戏 UI 元素作为识别模板

用法:
    # PC 客户端（星穹铁道 / 异环 / 终末地）
    python tools/capture_assets.py --game hsr --mode pc --window "星穹铁道"

    # 模拟器（火影忍者）
    python tools/capture_assets.py --game naruto --mode adb

流程:
    1. 截取游戏窗口画面
    2. 鼠标框选 ROI 区域
    3. 输入素材名称 → 保存到 games/<game>/assets/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import argparse
from pathlib import Path

# 全局变量
_selecting = False; _start_pt = None; _end_pt = None
_current_img = None; _display_img = None
_WINDOW_NAME = "素材采集 — 框选ROI | Enter保存 | Esc跳过 | s重新截图 | q退出"


class CaptureTool:
    """统一采集工具 — 支持 PC 窗口和 ADB"""

    # 星穹铁道素材清单
    HSR_ASSETS = [
        ("main_map_btn", "主界面-地图按钮"),
        ("main_quest_btn", "主界面-任务按钮"),
        ("main_char_btn", "主界面-角色按钮"),
        ("main_bag_btn", "主界面-背包按钮"),
        ("main_shop_btn", "主界面-商店按钮"),
        ("signin_entry", "签到入口"),
        ("signin_claim_btn", "签到领取按钮"),
        ("signin_done", "签到完成标识"),
        ("mail_entry", "邮件入口"),
        ("mail_claim_all", "一键领取按钮"),
        ("dispatch_entry", "派遣入口"),
        ("dispatch_claim_btn", "派遣收取按钮"),
        ("dispatch_redispatch_btn", "再次派遣按钮"),
        ("dispatch_confirm", "派遣确认按钮"),
        ("stamina_entry", "体力副本入口"),
        ("stamina_start_btn", "开始挑战按钮"),
        ("stamina_auto_btn", "自动战斗按钮"),
        ("stamina_complete", "通关完成标识"),
        ("stamina_use_item", "使用体力药确认"),
        ("loading_screen", "加载画面特征"),
        ("popup_close", "弹窗关闭按钮(右上X)"),
        ("daily_reset_popup", "每日重置弹窗"),
        ("network_retry_btn", "网络重试按钮"),
    ]

    MANIFESTS = {"hsr": HSR_ASSETS}

    def __init__(self, game_name: str, mode: str = "pc",
                 window_title: str = None, adb_path: str = "adb", adb_port: int = 16384):
        self.game_name = game_name
        self.mode = mode
        self.window_title = window_title
        self.adb_path = adb_path
        self.adb_port = adb_port

        self.game_dir = Path(__file__).parent.parent / "games" / game_name
        self.assets_dir = self.game_dir / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        (Path(__file__).parent.parent / "screenshots").mkdir(parents=True, exist_ok=True)

        self.device = None
        self._init_device()

    def _init_device(self):
        if self.mode == "pc":
            from core.win32_device import Win32Device
            title = self.window_title or self.game_name
            self.device = Win32Device(window_title=title)
            hwnd = self.device.hwnd
            if hwnd:
                w, h = self.device.get_resolution()
                print(f"✅ 找到窗口: {self.window_title} ({w}x{h})")
            else:
                print(f"⚠️ 未找到包含 '{title}' 的窗口")
                print("   请确认游戏已启动，或将窗口标题包含关键字")
        else:
            # ADB 模式
            import subprocess
            ports = [self.adb_port, 7555, 5555]
            for port in ports:
                result = subprocess.run(
                    [self.adb_path, "connect", f"127.0.0.1:{port}"],
                    capture_output=True, text=True, timeout=5
                )
                if "connected" in result.stdout.lower() or "already" in result.stdout.lower():
                    print(f"✅ ADB 已连接 127.0.0.1:{port}")
                    from core.device import AdbDevice
                    self.device = AdbDevice(host="127.0.0.1", port=port)
                    return
            print("⚠️ 未检测到模拟器")

    def capture(self) -> np.ndarray:
        """截取游戏画面"""
        if self.device is None:
            raise RuntimeError("设备未连接")
        return self.device.screenshot()

    def guided_capture(self):
        """引导式逐个采集"""
        items = self.MANIFESTS.get(self.game_name, [])
        if not items:
            print(f"❌ 无素材清单: {self.game_name}")
            return

        print(f"\n🎯 引导式采集 — {self.game_name} ({self.mode.upper()})")
        print(f"   共 {len(items)} 个素材\n")
        print(f"   操作: 🖱️ 框选 → Enter保存 → 输入名称")
        print(f"         Esc跳过 | s重新截图 | q退出\n")

        collected, skipped = [], []

        for asset_id, description in items:
            target_path = self.assets_dir / f"{asset_id}.png"
            if target_path.exists():
                print(f"  ⏭️  [{asset_id}] 已存在，跳过")
                skipped.append(asset_id)
                continue

            print(f"\n{'─'*50}")
            print(f"  🎯 [{asset_id}] {description}")
            print(f"    导航到对应界面后按 's' 重新截图，框选区域按 Enter")

            success = self._crop_loop(asset_id, target_path)
            if success:
                collected.append(asset_id)
            else:
                skipped.append(asset_id)

        cv2.destroyAllWindows()
        print(f"\n{'='*50}")
        print(f"  ✅ 已采集: {len(collected)} | ⏭️ 已跳过: {len(skipped)}")
        print(f"  素材目录: {self.assets_dir}")

    def _crop_loop(self, asset_id: str, target_path: Path) -> bool:
        """单素材框选循环"""
        global _selecting, _start_pt, _end_pt, _current_img, _display_img

        cv2.namedWindow(_WINDOW_NAME)
        cv2.setMouseCallback(_WINDOW_NAME, _mouse_callback)

        _start_pt = None
        _end_pt = None

        # 初始截图
        try:
            img = self.capture()
            _current_img = img.copy()
            h, w = img.shape[:2]
            scale = 1.0
            if w > 1400:
                scale = 1400 / w
                _display_img = cv2.resize(img, (int(w*scale), int(h*scale)))
            else:
                _display_img = img.copy()
        except Exception as e:
            print(f"  ❌ 截图失败: {e}")
            return False

        while True:
            show = _display_img.copy()

            # 绘制选择框
            if _start_pt and _end_pt:
                x1, y1 = _start_pt
                x2, y2 = _end_pt
                cv2.rectangle(show, (x1, y1), (x2, y2), (0, 255, 80), 2)
                rw = abs(x2-x1); rh = abs(y2-y1)
                cv2.putText(show, f"{rw}x{rh}", (x1+5, y1-8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,255,80), 2)

            cv2.putText(show, f"[{asset_id}]", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,200,80), 2)
            cv2.putText(show, "Enter=保存 | Esc=跳过 | s=重截 | q=退出",
                       (10, show.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX,
                       0.45, (160,160,160), 1)
            cv2.imshow(_WINDOW_NAME, show)

            key = cv2.waitKey(30) & 0xFF

            if key == 13:  # Enter - save
                if _start_pt and _end_pt:
                    name = input(f"  素材名 (回车='{asset_id}'): ").strip()
                    if not name:
                        name = asset_id

                    x1 = min(_start_pt[0], _end_pt[0])
                    y1 = min(_start_pt[1], _end_pt[1])
                    x2 = max(_start_pt[0], _end_pt[0])
                    y2 = max(_start_pt[1], _end_pt[1])

                    if scale != 1.0:
                        x1, x2 = int(x1/scale), int(x2/scale)
                        y1, y2 = int(y1/scale), int(y2/scale)

                    roi = _current_img[y1:y2, x1:x2]
                    save_path = self.assets_dir / f"{name}.png"
                    cv2.imwrite(str(save_path), roi)
                    print(f"  ✅ 已保存: {save_path} ({roi.shape[1]}x{roi.shape[0]})")
                    return True
                else:
                    print("  ⚠️ 请先框选区域")

            elif key == 27:  # Esc - skip
                return False

            elif key == ord('s'):  # rescreenshot
                print("  📸 重新截图...")
                try:
                    img = self.capture()
                    _current_img = img.copy()
                    h, w = img.shape[:2]
                    scale = 1.0
                    if w > 1400:
                        scale = 1400 / w
                        _display_img = cv2.resize(img, (int(w*scale), int(h*scale)))
                    else:
                        _display_img = img.copy()
                    _start_pt = None; _end_pt = None
                except Exception as e:
                    print(f"  ❌ 截图失败: {e}")

            elif key == ord('q'):
                return False

        return False


def _mouse_callback(event, x, y, flags, param):
    global _selecting, _start_pt, _end_pt
    if event == cv2.EVENT_LBUTTONDOWN:
        _selecting = True; _start_pt = (x, y); _end_pt = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and _selecting:
        _end_pt = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        _selecting = False; _end_pt = (x, y)


def main():
    parser = argparse.ArgumentParser(description="游戏 UI 素材采集工具")
    parser.add_argument("--game", default="hsr", help="游戏名称")
    parser.add_argument("--mode", default="pc", choices=["pc", "adb"])
    parser.add_argument("--window", type=str, help="窗口标题关键字 (PC模式)")
    parser.add_argument("--adb", type=str, default="adb", help="ADB 路径")
    parser.add_argument("--port", type=int, default=16384, help="ADB 端口")
    args = parser.parse_args()

    # 默认窗口标题
    window_title = args.window
    if args.mode == "pc" and not window_title:
        defaults = {"hsr": "星穹铁道", "yihuan": "异环", "zhongmodi": "终末地"}
        window_title = defaults.get(args.game, args.game)

    tool = CaptureTool(
        game_name=args.game,
        mode=args.mode,
        window_title=window_title,
        adb_path=args.adb,
        adb_port=args.port
    )

    if tool.device is None:
        print("\n❌ 设备初始化失败")
        if args.mode == "pc":
            print(f"   提示: 请确认游戏窗口标题包含 '{window_title}'")
            print(f"   用法: python tools/capture_assets.py --game hsr --mode pc --window \"窗口标题\"")
        sys.exit(1)

    tool.guided_capture()


if __name__ == '__main__':
    main()
