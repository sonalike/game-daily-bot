"""Asset capture tool — gameplay screenshot ROI cropper.

Usage:
    python tools/capture_assets.py --game hsr --window "星穹铁道"

In the OpenCV window:
    Mouse drag  = select region (red rectangle)
    SPACE/Enter = save selection and go to next asset
    S           = take a new screenshot
    C           = skip current asset
    Q / Esc     = quit

IMPORTANT: Close the window by pressing Q (NOT clicking X on the title bar).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import cv2, argparse
import numpy as np
from pathlib import Path

WIN = "Asset Capture [Q=quit S=snap SPACE=save C=skip]"

# Mouse state
_dragging = False
_p1 = None
_p2 = None


def _on_mouse(event, x, y, flags, param):
    global _dragging, _p1, _p2
    if event == cv2.EVENT_LBUTTONDOWN:
        _dragging = True
        _p1 = (x, y)
        _p2 = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and _dragging:
        _p2 = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        _dragging = False
        _p2 = (x, y)


def _draw_rect(img, p1, p2):
    """Draw a red selection rectangle"""
    if p1 and p2:
        x1, y1 = p1; x2, y2 = p2
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(img, f"{abs(x2-x1)}x{abs(y2-y1)}",
                   (x1+4, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)


class CaptureTool:
    def __init__(self, game, window_title):
        self.project = Path(__file__).parent.parent
        self.assets = self.project / "games" / game / "assets"
        self.assets.mkdir(parents=True, exist_ok=True)

        from core.win32_device import Win32Device
        self.dev = Win32Device(window_title=window_title)
        if not self.dev.hwnd:
            print(f"ERROR: No window found matching '{window_title}'")
            sys.exit(1)
        print(f"OK: [{self.dev.get_resolution()[0]}x{self.dev.get_resolution()[1]}]")

    def snap(self):
        return self.dev.screenshot()

    def run(self, items):
        global _p1, _p2

        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(WIN, _on_mouse)
        cv2.resizeWindow(WIN, 1280, 720)
        cv2.moveWindow(WIN, 50, 50)

        collected, skipped = [], []
        img = None
        idx = 0
        total = len(items)

        print(f"\nTotal: {total} assets\n")

        while idx < total:
            asset_id, desc = items[idx]
            path = self.assets / f"{asset_id}.png"

            if path.exists():
                print(f"  [{idx+1}/{total}] SKIP (exists): {asset_id}")
                skipped.append(asset_id)
                idx += 1
                continue

            # Need screenshot?
            if img is None:
                print(f"\n  [{idx+1}/{total}] {asset_id}: {desc}")
                print(f"    Press 'S' to take screenshot...")

                while True:
                    prompt = np.zeros((300, 640, 3), dtype=np.uint8)
                    cv2.putText(prompt, f"[{idx+1}/{total}] {asset_id}: {desc}", (20, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 200, 80), 2)
                    cv2.putText(prompt, "S = Screenshot | C = Skip | Q = Quit", (20, 150),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 2)
                    cv2.imshow(WIN, prompt)

                    k = cv2.waitKey(100) & 0xFF
                    if k == ord('s'):
                        try:
                            img = self.snap()
                            _p1 = _p2 = None
                            print(f"    Ready ({img.shape[1]}x{img.shape[0]}). Drag to select, SPACE to save.")
                            break
                        except Exception as e:
                            print(f"    Screenshot error: {e}")
                    elif k == ord('c'):
                        print(f"    SKIPPED")
                        skipped.append(asset_id)
                        idx += 1
                        break
                    elif k == ord('q') or k == 27:
                        print("Quit.")
                        cv2.destroyAllWindows()
                        return

                if img is None:
                    continue

            # Selection loop
            while True:
                display = img.copy()
                _draw_rect(display, _p1, _p2)
                cv2.putText(display, f"[{idx+1}/{total}] {asset_id}: {desc}", (10, 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 60), 2)
                cv2.putText(display, "SPACE=save | C=skip | S=resnap | Q=quit",
                           (10, display.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

                cv2.imshow(WIN, display)
                k = cv2.waitKey(50) & 0xFF

                if k == 32 or k == 13:  # Space / Enter
                    if _p1 and _p2:
                        x1, x2 = sorted([_p1[0], _p2[0]])
                        y1, y2 = sorted([_p1[1], _p2[1]])
                        if x2 > x1 and y2 > y1:
                            crop = img[y1:y2, x1:x2]
                            cv2.imwrite(str(path), crop)
                            print(f"    SAVED: {asset_id}.png ({x2-x1}x{y2-y1})")
                            collected.append(asset_id)
                            idx += 1
                            img = None
                            _p1 = _p2 = None
                            break
                    # else: no selection yet, ignore

                elif k == ord('c'):
                    print(f"    SKIPPED: {asset_id}")
                    skipped.append(asset_id)
                    idx += 1
                    img = None
                    _p1 = _p2 = None
                    break

                elif k == ord('s'):
                    try:
                        img = self.snap()
                        _p1 = _p2 = None
                        print(f"    Re-captured ({img.shape[1]}x{img.shape[0]})")
                    except Exception as e:
                        print(f"    Error: {e}")

                elif k == ord('q') or k == 27:
                    print("Quit.")
                    cv2.destroyAllWindows()
                    return

        cv2.destroyAllWindows()
        print(f"\nDone! Collected: {len(collected)} | Skipped: {len(skipped)}")
        print(f"Assets: {self.assets.resolve()}")


# — Asset manifest —
HSR = [
    ("enter_game_btn",          "主界面 '进入游戏' 按钮"),
    ("loading_screen",          "加载画面特征"),
    ("menu_panel",              "按Esc后的菜单栏面板"),
    ("menu_mail_btn",           "菜单栏→邮箱按钮"),
    ("menu_assign_btn",         "菜单栏→委托按钮"),
    ("menu_guide_btn",          "菜单栏→星际和平指南按钮"),
    ("mail_claim_all_highlight","邮箱→全部领取按钮(高亮)"),
    ("assign_claim_btn",        "委托→领取奖励按钮"),
    ("assign_close_area",       "委托→关闭领取窗口空白处"),
    ("guide_char_train_btn",    "指南→角色培养按钮"),
    ("char_train_enter_btn",    "角色培养→进入按钮"),
    ("dungeon_select_screen",   "副本选关界面特征"),
    ("dungeon_challenge_btn",   "副本选关→挑战按钮"),
    ("team_start_btn",          "队伍配置→开始挑战"),
    ("battle_auto_btn",         "战斗→自动战斗按钮"),
    ("battle_victory_screen",   "挑战成功界面"),
    ("exit_stage_btn",          "挑战成功→退出关卡"),
    ("guide_bottom_claim_btn",  "指南→下方领取奖励"),
    ("guide_reward_tier1",      "指南奖励→100档"),
    ("guide_reward_tier2",      "指南奖励→200档"),
    ("guide_reward_tier3",      "指南奖励→300档"),
    ("guide_reward_tier4",      "指南奖励→400档"),
    ("guide_reward_tier5",      "指南奖励→500档"),
    ("guide_daily_training_claim","指南→每日实训奖励领取"),
]

MANIFESTS = {"hsr": HSR}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="hsr")
    ap.add_argument("--window", type=str)
    args = ap.parse_args()

    window = args.window or "星穹铁道"
    items = MANIFESTS.get(args.game, [])
    if not items:
        print(f"No manifest for '{args.game}'")
        sys.exit(1)

    print(f"Asset Capture | {args.game} | {len(items)} items")
    tool = CaptureTool(args.game, window)
    tool.run(items)


if __name__ == "__main__":
    main()
