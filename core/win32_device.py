"""Win32 设备 — PC 客户端窗口截图 + 键鼠模拟"""
import time
import ctypes
import ctypes.wintypes
from ctypes import wintypes
import numpy as np
from core.device import Device

# Win32 API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

# ── 常量 ──
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
SM_CXSCREEN = 0
SM_CYSCREEN = 1

# ── 结构体 ──
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


class Win32Device(Device):
    """PC 客户端窗口 — 截图 + 键鼠模拟"""

    def __init__(self, window_title: str = None, process_name: str = None):
        """
        window_title: 窗口标题关键字（如 "崩坏：星穹铁道"）
        process_name: 进程名（如 "StarRail.exe"）
        """
        self.window_title = window_title
        self.process_name = process_name
        self._hwnd = None
        self._window_rect = None
        self._screenshotter = None  # lazy init mss

    @property
    def hwnd(self):
        """获取窗口句柄"""
        if self._hwnd is None:
            self._find_window()
        return self._hwnd

    def _find_window(self):
        """查找游戏窗口"""
        # 按标题查找
        if self.window_title:
            # 枚举所有顶层窗口
            result = []

            def enum_callback(hwnd, lParam):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    title = buf.value
                    if self.window_title.lower() in title.lower():
                        result.append(hwnd)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

            if result:
                self._hwnd = result[0]
                return

        # 按进程名查找
        if self.process_name:
            import subprocess
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {self.process_name}',
                 '/FO', 'CSV', '/NH'],
                capture_output=True, text=True
            )
            if self.process_name.lower() in result.stdout.lower():
                # 找到了进程，通过进程名匹配窗口
                process_lower = self.process_name.lower()

                def enum_callback2(hwnd, lParam):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        # 获取进程ID
                        pid = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        if buf.value:
                            result.append((hwnd, buf.value))
                    return True

                result.clear()
                user32.EnumWindows(WNDENUMPROC(enum_callback2), 0)
                for hwnd, title in result:
                    if title:  # 找有标题的非空窗口
                        self._hwnd = hwnd
                        return

        self._hwnd = None
        return

    def _get_window_rect(self) -> tuple[int, int, int, int]:
        """获取窗口屏幕坐标 (left, top, right, bottom)"""
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        # 对于高DPI，GetWindowRect 返回的是缩放后的坐标
        # 需要获取实际客户区大小用于截图
        return (rect.left, rect.top, rect.right, rect.bottom)

    def _bring_to_foreground(self):
        """将游戏窗口置于前台"""
        if self.hwnd:
            # 恢复最小化
            user32.ShowWindow(self.hwnd, SW_RESTORE)
            user32.SetForegroundWindow(self.hwnd)
            time.sleep(0.3)

    def screenshot(self) -> np.ndarray:
        """截取游戏窗口画面"""
        import mss
        import mss.tools

        self._bring_to_foreground()
        left, top, right, bottom = self._get_window_rect()

        with mss.mss() as sct:
            monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}
            img = sct.grab(monitor)
            # mss returns BGRA, convert to BGR
            arr = np.array(img)
            return arr[:, :, :3]  # drop alpha channel

    def tap(self, x: int, y: int):
        """点击窗口内相对坐标"""
        self._bring_to_foreground()
        left, top, _, _ = self._get_window_rect()

        # 转换为屏幕绝对坐标
        screen_x = left + x
        screen_y = top + y

        # 移动鼠标
        self._send_mouse_move(screen_x, screen_y)
        time.sleep(0.05)
        # 点击
        self._send_mouse_click()
        time.sleep(0.05)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """模拟拖拽（用于需要滑动的场景）"""
        self._bring_to_foreground()
        left, top, _, _ = self._get_window_rect()

        screen_x1, screen_y1 = left + x1, top + y1
        screen_x2, screen_y2 = left + x2, top + y2

        # 按下
        self._send_mouse_move(screen_x1, screen_y1)
        self._send_mouse_down()
        # 分步移动
        steps = max(10, duration // 15)
        for i in range(1, steps + 1):
            t = i / steps
            cur_x = int(screen_x1 + (screen_x2 - screen_x1) * t)
            cur_y = int(screen_y1 + (screen_y2 - screen_y1) * t)
            self._send_mouse_move(cur_x, cur_y)
            time.sleep(duration / 1000 / steps)
        # 释放
        self._send_mouse_up()

    def get_resolution(self) -> tuple[int, int]:
        """返回窗口宽高"""
        left, top, right, bottom = self._get_window_rect()
        return (right - left, bottom - top)

    # ── 底层 SendInput 封装 ──

    def _send_input(self, *inputs: INPUT):
        """发送输入事件"""
        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        user32.SendInput(n, arr, ctypes.sizeof(INPUT))

    def _send_mouse_move(self, x: int, y: int):
        """移动鼠标到绝对屏幕坐标"""
        screen_w = user32.GetSystemMetrics(SM_CXSCREEN)
        screen_h = user32.GetSystemMetrics(SM_CYSCREEN)
        # 绝对坐标: 0-65535 范围
        abs_x = int(x * 65535 / screen_w)
        abs_y = int(y * 65535 / screen_h)

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dx = abs_x
        inp.union.mi.dy = abs_y
        inp.union.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
        self._send_input(inp)

    def _send_mouse_click(self):
        """鼠标左键点击"""
        # 按下
        inp_down = INPUT()
        inp_down.type = INPUT_MOUSE
        inp_down.union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        self._send_input(inp_down)
        time.sleep(0.02)
        # 释放
        inp_up = INPUT()
        inp_up.type = INPUT_MOUSE
        inp_up.union.mi.dwFlags = MOUSEEVENTF_LEFTUP
        self._send_input(inp_up)

    def _send_mouse_down(self):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        self._send_input(inp)

    def _send_mouse_up(self):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi.dwFlags = MOUSEEVENTF_LEFTUP
        self._send_input(inp)

    def press_key(self, key_code: int):
        """按下并释放键盘按键"""
        # 按下
        inp_down = INPUT()
        inp_down.type = INPUT_KEYBOARD
        inp_down.union.ki.wVk = key_code
        self._send_input(inp_down)
        time.sleep(0.05)
        # 释放
        inp_up = INPUT()
        inp_up.type = INPUT_KEYBOARD
        inp_up.union.ki.wVk = key_code
        inp_up.union.ki.dwFlags = KEYEVENTF_KEYUP
        self._send_input(inp_up)
