"""图像识别引擎 — 模板匹配 + OCR + 特征检测"""
import cv2
import numpy as np
import time
from pathlib import Path
from typing import Optional, Callable


class Vision:
    """图像识别引擎"""

    def __init__(self, assets_dir: str = None):
        self.assets_dir = Path(assets_dir) if assets_dir else None

    def _load_template(self, path: str) -> np.ndarray:
        """加载模板图片"""
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"模板图片不存在: {path}")
        return img

    def find(self, template_path: str, screenshot: np.ndarray,
             threshold: float = 0.85) -> Optional[tuple[int, int]]:
        """在截图中查找模板，返回中心点坐标 (x, y)，未找到返回 None"""
        if screenshot is None:
            raise ValueError("screenshot is required")

        template = self._load_template(template_path)
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)
        return None

    def exists(self, template_path: str, screenshot: np.ndarray,
               threshold: float = 0.85) -> bool:
        """模板是否存在"""
        return self.find(template_path, screenshot, threshold) is not None

    def wait_for(self, screenshot_provider: Callable[[], np.ndarray],
                 template_path: str, timeout: float = 10,
                 interval: float = 0.5) -> Optional[tuple[int, int]]:
        """等待模板出现，超时返回 None"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            screenshot = screenshot_provider()
            pos = self.find(template_path, screenshot)
            if pos is not None:
                return pos
            time.sleep(interval)
        return None

    def wait_until_gone(self, screenshot_provider: Callable[[], np.ndarray],
                        template_path: str, timeout: float = 30,
                        interval: float = 0.5) -> bool:
        """等待模板消失，超时返回 False"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            screenshot = screenshot_provider()
            if not self.exists(template_path, screenshot):
                return True
            time.sleep(interval)
        return False
