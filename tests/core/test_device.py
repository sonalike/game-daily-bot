import pytest
import numpy as np
from core.device import Device, AdbDevice


class FakeDevice(Device):
    """用于测试抽象接口的具体实现"""

    def screenshot(self):
        return np.zeros((1080, 1920, 3), dtype=np.uint8)

    def tap(self, x, y):
        self._last_tap = (x, y)

    def swipe(self, x1, y1, x2, y2, duration=300):
        self._last_swipe = (x1, y1, x2, y2, duration)

    def get_resolution(self):
        return (1920, 1080)


def test_device_abstract():
    """验证无法直接实例化 Device"""
    with pytest.raises(TypeError):
        Device()


def test_device_concrete():
    d = FakeDevice()
    img = d.screenshot()
    assert isinstance(img, np.ndarray)
    assert img.shape == (1080, 1920, 3)


def test_device_tap():
    d = FakeDevice()
    d.tap(100, 200)
    assert d._last_tap == (100, 200)


def test_device_swipe():
    d = FakeDevice()
    d.swipe(0, 100, 200, 100, 500)
    assert d._last_swipe == (0, 100, 200, 100, 500)


def test_device_get_resolution():
    d = FakeDevice()
    assert d.get_resolution() == (1920, 1080)


def test_device_wait():
    import time
    d = FakeDevice()
    start = time.time()
    d.wait(0.1)
    elapsed = time.time() - start
    assert 0.09 < elapsed < 0.2
