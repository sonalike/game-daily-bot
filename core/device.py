"""设备抽象层 — 统一接口，支持 ADB 和云游戏后端"""

from abc import ABC, abstractmethod
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
    """ADB 设备实现（暂为占位符）"""

    def screenshot(self) -> np.ndarray:
        raise NotImplementedError

    def tap(self, x: int, y: int):
        raise NotImplementedError

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        raise NotImplementedError

    def get_resolution(self) -> tuple[int, int]:
        raise NotImplementedError
