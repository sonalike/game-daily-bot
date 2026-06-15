"""Asset capture tool — crop UI elements from game screenshots.

Usage:
    python tools/capture_assets.py --game hsr --window "Star Rail"

Mouse controls in the OpenCV window:
    Drag to select ROI → Enter to save → type name → repeat
    s = new screenshot | Esc = skip | q = quit
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import cv2, numpy as np, argparse
from pathlib import Path

# — Globals —
_sel = False; _p1 = None; _p2 = None; _img = None; _disp = None; _scale = 1.0
WIN = "Asset Capture"  # ASCII only — avoids OpenCV title encoding issues on Windows


def _on_mouse(event, x, y, flags, param):
    global _sel, _p1, _p2
    if event == cv2.EVENT_LBUTTONDOWN:
        _sel = True; _p1 = (x, y); _p2 = (x, y)
    elif event == cv2.EVENT_MOUSEMOVE and _sel:
        _p2 = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        _sel = False; _p2 = (x, y)


def _show(img, label=""):
    """Return (updated _display_img, scale) — resize if needed"""
    h, w = img.shape[:2]
    s = 1.0
    if w > 1400:
        s = 1400 / w
    if s != 1.0:
        img = cv2.resize(img, (int(w * s), int(h * s)))
    return img, s


class CaptureTool:
    def __init__(self, game: str, window_title: str):
        self.game = game
        self.assets = Path(f"games/{game}/assets")
        self.assets.mkdir(parents=True, exist_ok=True)
        Path("screenshots").mkdir(exist_ok=True)

        from core.win32_device import Win32Device
        self.dev = Win32Device(window_title=window_title)
        self.hwnd = self.dev.hwnd
        if not self.hwnd:
            print(f"ERROR: No window matching '{window_title}' found.")
            print("  Make sure the game is running and visible.")
            sys.exit(1)
        w, h = self.dev.get_resolution()
        print(f"OK: Found game window [{w}x{h}]")

    def snap(self):
        return self.dev.screenshot()

    def run(self, items: list[tuple[str, str]]):
        global _sel, _p1, _p2, _img, _disp, _scale

        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(WIN, _on_mouse)
        mvx, mvy = 100, 80  # position the cv2 window
        cv2.moveWindow(WIN, mvx, mvy)

        collected, skipped = [], []
        total = len(items)

        for idx, (asset_id, desc) in enumerate(items):
            path = self.assets / f"{asset_id}.png"
            if path.exists():
                print(f"  [{idx+1}/{total}] SKIP {asset_id} — already exists")
                skipped.append(asset_id)
                continue

            # Take screenshot
            print(f"\n  [{idx+1}/{total}] {asset_id}: {desc}")
            print(f"    -> Navigate to the right screen, then press 's' in the CV window")
            _img = None
            waiting = True
            while waiting:
                show = np.zeros((300, 500, 3), dtype=np.uint8)
                cv2.putText(show, f"Press 's' to capture", (50, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                cv2.putText(show, f"[{idx+1}/{total}] {asset_id}: {desc}", (50, 130),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 180, 80), 2)
                cv2.putText(show, f"q=quit  s=snap  Esc=skip", (50, 180),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1)
                cv2.imshow(WIN, show)

                key = cv2.waitKey(50) & 0xFF
                if key == ord('s'):
                    try:
                        raw = self.snap()
                        _img, _scale = _show(raw)
                        _p1 = _p2 = None
                        waiting = False
                        print("    Screenshot ready. Drag to select ROI, Enter to save.")
                    except Exception as e:
                        print(f"    ERROR: {e}")
                elif key == 27:  # Esc
                    print(f"    SKIPPED")
                    skipped.append(asset_id)
                    waiting = False
                elif key == ord('q'):
                    print("QUIT")
                    cv2.destroyAllWindows()
                    return

            if _img is None:
                continue

            # Selection loop
            _disp = _img.copy()
            cv2.resizeWindow(WIN, _disp.shape[1], _disp.shape[0])
            cv2.moveWindow(WIN, mvx, mvy)

            selecting = True
            while selecting:
                show = _disp.copy()
                if _p1 and _p2:
                    x1, y1 = _p1; x2, y2 = _p2
                    cv2.rectangle(show, (x1, y1), (x2, y2), (0, 255, 60), 2)
                    rw, rh = abs(x2-x1), abs(y2-y1)
                    cv2.putText(show, f"{rw}x{rh}", (x1+4, y1-6),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 60), 2)
                cv2.putText(show, f"{asset_id}: {desc}", (10, 22),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 180, 60), 2)
                cv2.putText(show, "Enter=save | Esc=skip | s=re-capture",
                           (10, show.shape[0]-8), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1)
                cv2.imshow(WIN, show)

                key = cv2.waitKey(50) & 0xFF
                if key == 13 and _p1 and _p2:  # Enter
                    name = input(f"    Asset name (Enter='{asset_id}'): ").strip()
                    if not name:
                        name = asset_id
                    x1, y1 = _p1; x2, y2 = _p2
                    x1, x2 = sorted([int(x1/_scale), int(x2/_scale)])
                    y1, y2 = sorted([int(y1/_scale), int(y2/_scale)])
                    roi = _img[y1:y2, x1:x2]
                    save_path = self.assets / f"{name}.png"
                    cv2.imwrite(str(save_path), roi)
                    print(f"    SAVED: {save_path} ({roi.shape[1]}x{roi.shape[0]})")
                    collected.append(asset_id)
                    selecting = False
                elif key == 27:
                    print(f"    SKIPPED")
                    skipped.append(asset_id)
                    selecting = False
                elif key == ord('s'):
                    try:
                        raw = self.snap()
                        _img, _scale = _show(raw)
                        _disp = _img.copy()
                        cv2.resizeWindow(WIN, _disp.shape[1], _disp.shape[0])
                        cv2.moveWindow(WIN, mvx, mvy)
                        _p1 = _p2 = None
                        print("    Re-captured.")
                    except Exception as e:
                        print(f"    ERROR: {e}")
                elif key == ord('q'):
                    print("QUIT")
                    cv2.destroyAllWindows()
                    return

        cv2.destroyAllWindows()
        print(f"\n{'='*50}")
        print(f"  Done! Collected: {len(collected)} | Skipped: {len(skipped)}")
        print(f"  Assets dir: {self.assets.resolve()}")


# — Asset manifests —
HSR = [
    ("signin_entry",      "Sign-in entry button"),
    ("signin_claim",      "Sign-in claim button"),
    ("signin_done",       "Sign-in done indicator"),
    ("mail_entry",        "Mail entry button"),
    ("mail_claim_all",    "Claim all mail button"),
    ("dispatch_entry",    "Dispatch entry button"),
    ("dispatch_claim",    "Dispatch claim button"),
    ("dispatch_redispatch","Dispatch re-dispatch button"),
    ("dispatch_confirm",  "Dispatch confirm button"),
    ("stamina_entry",     "Stamina dungeon entry"),
    ("stamina_start",     "Start challenge button"),
    ("stamina_auto",      "Auto-battle toggle"),
    ("stamina_complete",  "Stage complete indicator"),
    ("stamina_use_item",  "Use stamina refill confirm"),
    ("loading_indicator", "Loading screen indicator"),
    ("popup_close",       "Popup close button (X)"),
    ("network_retry",     "Network error retry button"),
    ("back_btn",          "Generic back button"),
]

MANIFESTS = {"hsr": HSR}


def main():
    ap = argparse.ArgumentParser(description="Game UI asset capture tool")
    ap.add_argument("--game", default="hsr")
    ap.add_argument("--window", type=str, help="Game window title substring")
    args = ap.parse_args()

    window = args.window
    if not window:
        defaults = {"hsr": "星穹铁道", "yihuan": "异环", "zhongmodi": "终末地"}
        window = defaults.get(args.game, args.game)

    items = MANIFESTS.get(args.game, [])
    if not items:
        print(f"No asset manifest for game '{args.game}'")
        sys.exit(1)

    print(f"Asset Capture — {args.game} ({len(items)} items)")
    print(f"Looking for window: '{window}'\n")

    tool = CaptureTool(args.game, window)
    tool.run(items)


if __name__ == "__main__":
    main()
