"""设备抽象层 — 统一接口，支持 ADB 和云游戏后端"""

from abc import ABC, abstractmethod
import subprocess
import time

import numpy as np


class Device(ABC):
    """设备抽象基类"""

    @abstractmethod
    def screenshot(self) -> np.ndarray:
        """截取当前屏幕，返回 BGR numpy 数组 (H, W, 3)"""
        ...

    @abstractmethod
    def tap(self, x: int, y: int):
        """点击指定坐标"""
        ...

    @abstractmethod
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """从 (x1,y1) 滑动到 (x2,y2)，持续 duration 毫秒"""
        ...

    @abstractmethod
    def get_resolution(self) -> tuple[int, int]:
        """返回 (width, height)"""
        ...

    def wait(self, seconds: float):
        """等待指定秒数"""
        time.sleep(seconds)


class AdbDevice(Device):
    """通过 ADB 连接 MuMu 模拟器"""

    def __init__(self, host: str = '127.0.0.1', port: int = 7555):
        self.host = host
        self.port = port
        self.serial = f'{host}:{port}'
        self._resolution = None

    def _adb(self, *args, timeout: int = 10, text: bool = True) -> subprocess.CompletedProcess:
        """执行 ADB 命令"""
        cmd = ['adb', '-s', self.serial] + list(args)
        return subprocess.run(cmd, capture_output=True, text=text, timeout=timeout)

    def connect(self) -> bool:
        """连接设备"""
        result = subprocess.run(
            ['adb', 'connect', self.serial],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0

    def screenshot(self) -> np.ndarray:
        """通过 ADB 获取屏幕截图"""
        import cv2

        result = self._adb('exec-out', 'screencap', '-p', text=False)
        if result.returncode != 0:
            raise RuntimeError(f"截图失败: {result.stderr}")

        img_array = np.frombuffer(result.stdout, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("截图解码失败")
        return img

    def tap(self, x: int, y: int):
        result = self._adb('shell', 'input', 'tap', str(x), str(y), timeout=5)
        if result.returncode != 0:
            raise RuntimeError(f"点击失败: {result.stderr}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        result = self._adb('shell', 'input', 'swipe',
                  str(x1), str(y1), str(x2), str(y2), str(duration),
                  timeout=5)
        if result.returncode != 0:
            raise RuntimeError(f"滑动失败: {result.stderr}")

    def get_resolution(self) -> tuple[int, int]:
        if self._resolution is not None:
            return self._resolution
        try:
            result = self._adb('shell', 'wm', 'size')
            # Parse output: "Physical size: 1920x1080" or "1920x1080"
            output = result.stdout.strip()
            # Take the last line (Physical size takes precedence over Override size)
            for line in reversed(output.splitlines()):
                line = line.strip()
                if 'x' in line and any(c.isdigit() for c in line):
                    # Extract "WxH" pattern
                    size_str = line.split(':')[-1].strip()
                    if 'x' in size_str:
                        w_str, h_str = size_str.split('x')[:2]
                        w, h = int(w_str), int(h_str)
                        if w > 0 and h > 0:
                            self._resolution = (w, h)
                            return self._resolution
            raise ValueError(f"无法解析分辨率输出: {output}")
        except (ValueError, AttributeError) as e:
            raise RuntimeError(f"获取分辨率失败: {e}") from e
