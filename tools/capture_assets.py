"""Asset capture tool — crop UI elements using OpenCV selectROI.

Usage:
    python tools/capture_assets.py --game hsr --window "星穹铁道"

How to use the ROI selection window:
    - Drag mouse to select the region
    - Press SPACE or ENTER to confirm selection
    - Press C to cancel / skip
    - Press S to take a new screenshot
    - Press Q or ESC to quit
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import cv2, argparse
from pathlib import Path

WIN = "ROI Selector"


class CaptureTool:
    def __init__(self, game: str, window_title: str):
        self.game = game
        self.assets = Path(f"games/{game}/assets")
        self.assets.mkdir(parents=True, exist_ok=True)
        Path("screenshots").mkdir(exist_ok=True)

        from core.win32_device import Win32Device
        self.dev = Win32Device(window_title=window_title)
        if not self.dev.hwnd:
            print(f"ERROR: No window matching '{window_title}' found.")
            sys.exit(1)
        w, h = self.dev.get_resolution()
        print(f"OK: Found game window [{w}x{h}]")

    def snap(self):
        return self.dev.screenshot()

    def run(self, items: list[tuple[str, str]]):
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        # Resize display to fit screen (max 90% of 1920x1080)
        screen = _snap_screen_size()
        if screen:
            max_w = int(screen[0] * 0.85)
            max_h = int(screen[1] * 0.80)
            cv2.resizeWindow(WIN, max_w, max_h)
        cv2.moveWindow(WIN, 40, 40)

        collected, skipped = [], []
        img = None
        total = len(items)
        idx = 0

        print(f"\nTotal: {total} assets to capture")
        print("SPACE/ENTER = confirm | C = skip | S = new screenshot | Q = quit\n")

        while idx < total:
            asset_id, desc = items[idx]
            path = self.assets / f"{asset_id}.png"

            if path.exists():
                print(f"  [{idx+1}/{total}] SKIP {asset_id} — already exists")
                skipped.append(asset_id)
                idx += 1
                continue

            # Take screenshot if needed
            if img is None:
                print(f"  [{idx+1}/{total}] {asset_id}: {desc}")
                print(f"    Press 'S' to capture screenshot...")
                img = None
                # Wait for user to press S
                while True:
                    # Show a prompt image
                    prompt = _make_prompt(f"[{idx+1}/{total}] {asset_id}: {desc}",
                                          "Press S to capture | Q to quit")
                    cv2.imshow(WIN, prompt)
                    k = cv2.waitKey(100) & 0xFF
                    if k == ord('s'):
                        try:
                            raw = self.snap()
                            img = raw.copy()
                            print(f"    Screenshot ready ({img.shape[1]}x{img.shape[0]})")
                            break
                        except Exception as e:
                            print(f"    Error: {e}")
                    elif k == ord('q') or k == 27:
                        cv2.destroyAllWindows()
                        print("Quit.")
                        return
                    elif k == ord('c'):
                        print(f"    SKIPPED")
                        skipped.append(asset_id)
                        idx += 1
                        img = None
                        break

                if img is None:
                    continue

            # Show image and let user select ROI
            cv2.imshow(WIN, img)
            roi = cv2.selectROI(WIN, img, showCrosshair=True, fromCenter=False)

            # selectROI returns (x, y, w, h)
            x, y, w, h = roi

            if w > 0 and h > 0:
                # Valid selection — save
                crop = img[y:y+h, x:x+w]
                cv2.imwrite(str(path), crop)
                print(f"    SAVED: {asset_id}.png ({w}x{h})")
                collected.append(asset_id)
                idx += 1
                img = None  # reset for next item
            elif w == 0 and h == 0:
                # User pressed C (cancel) or closed the ROI window
                print(f"    SKIPPED (cancelled)")
                skipped.append(asset_id)
                idx += 1
            # If negative, user pressed something else, try again

        cv2.destroyAllWindows()
        print(f"\n{'='*50}")
        print(f"  Done! Collected: {len(collected)} | Skipped: {len(skipped)}")
        print(f"  Assets dir: {self.assets.resolve()}")
        print(f"{'='*50}")


def _make_prompt(title: str, hint: str) -> "np.ndarray":
    """Create a prompt display image"""
    import numpy as np
    img = np.zeros((300, 640, 3), dtype=np.uint8)
    cv2.putText(img, title, (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 200, 100), 2)
    cv2.putText(img, hint, (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    cv2.putText(img, "S=Capture  C=Skip  Q=Quit", (30, 220),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1)
    return img


def _snap_screen_size():
    """Get primary monitor resolution"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        w = root.winfo_screenwidth()
        h = root.winfo_screenheight()
        root.destroy()
        return (w, h)
    except:
        return None


# — 崩坏：星穹铁道 素材清单（使用游戏内实际名称）—
HSR = [
    # === 主界面 ===
    ("main_guide_btn",        "星际和平指南按钮"),

    # === 每日实训（签到）===
    ("daily_training_entry",  "每日实训入口"),
    ("daily_training_claim",  "每日实训领取按钮"),
    ("daily_training_done",   "每日实训完成标识"),

    # === 邮件 ===
    ("mail_entry",            "邮件入口"),
    ("mail_claim_all",        "一键领取按钮"),

    # === 委托（Assignments）===
    ("assign_entry",          "委托入口"),
    ("assign_claim",          "委托收取按钮"),
    ("assign_redispatch",     "再次委托按钮"),
    ("assign_confirm",        "委托确认按钮"),

    # === 清体力（拟造花萼/侵蚀隧洞）===
    ("stamina_dungeon",       "体力副本入口（花萼/隧洞）"),
    ("stamina_start",         "开始挑战按钮"),
    ("stamina_auto",          "自动战斗开关"),
    ("stamina_complete",      "通关完成"),
    ("stamina_refill",        "使用体力药确认"),

    # === 通用 ===
    ("loading_indicator",     "加载画面特征"),
    ("popup_close",           "弹窗关闭(X)"),
    ("network_retry",         "网络重试"),
    ("back_btn",              "返回按钮"),
]

MANIFESTS = {"hsr": HSR}


def main():
    ap = argparse.ArgumentParser(description="Game UI asset capture")
    ap.add_argument("--game", default="hsr")
    ap.add_argument("--window", type=str)
    args = ap.parse_args()

    window = args.window
    if not window:
        defaults = {"hsr": "星穹铁道", "yihuan": "异环", "zhongmodi": "终末地"}
        window = defaults.get(args.game, args.game)

    items = MANIFESTS.get(args.game, [])
    if not items:
        print(f"No manifest for '{args.game}'")
        sys.exit(1)

    print(f"Asset Capture — {args.game} ({len(items)} items)")
    print(f"Window: '{window}'\n")

    tool = CaptureTool(args.game, window)
    tool.run(items)


if __name__ == "__main__":
    main()
