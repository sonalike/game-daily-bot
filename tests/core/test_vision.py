import pytest
import numpy as np
import cv2
import os
import tempfile
from core.vision import Vision


class TestVision:
    @pytest.fixture
    def vision(self):
        return Vision()

    @pytest.fixture
    def sample_screen(self):
        """200x200 simulated game screen with a patterned 'button' (has variance)"""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        # Gray button with a white inner stripe
        img[80:100, 80:120] = (180, 180, 180)
        img[85:95, 85:115] = (255, 255, 255)
        return img

    @pytest.fixture
    def template_path(self):
        """Template similar to the button but with small noise (correlation ~0.988)"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            template = np.full((20, 40, 3), 180, dtype=np.uint8)
            template[5:15, 5:35] = (255, 255, 255)
            # Add deterministic noise so template is not perfectly identical
            noise = np.random.RandomState(42).randint(-10, 11, template.shape, dtype=np.int16)
            template = np.clip(template.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            cv2.imwrite(f.name, template)
            path = f.name
        yield path
        os.unlink(path)

    def test_find_returns_position(self, vision, sample_screen, template_path):
        """Template matching should find the button"""
        result = vision.find(template_path, sample_screen)
        assert result is not None
        x, y = result
        assert 80 <= x <= 120
        assert 80 <= y <= 100

    def test_find_returns_none_when_no_match(self, vision):
        """Non-existent template should return None"""
        black_screen = np.zeros((200, 200, 3), dtype=np.uint8)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            template = np.full((30, 30, 3), 200, dtype=np.uint8)
            template[5:25, 5:25] = (100, 100, 100)
            cv2.imwrite(f.name, template)
            path = f.name
        result = vision.find(path, black_screen)
        os.unlink(path)
        assert result is None

    def test_exists(self, vision, sample_screen, template_path):
        assert vision.exists(template_path, sample_screen) is True

    def test_exists_false(self, vision):
        black_screen = np.zeros((200, 200, 3), dtype=np.uint8)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            template = np.full((30, 30, 3), 200, dtype=np.uint8)
            template[5:25, 5:25] = (100, 100, 100)
            cv2.imwrite(f.name, template)
            path = f.name
        result = vision.exists(path, black_screen)
        os.unlink(path)
        assert result is False

    def test_find_with_threshold(self, vision, sample_screen, template_path):
        """Threshold 0.99 should NOT match (template has noise, correlation ~0.988)"""
        result = vision.find(template_path, sample_screen, threshold=0.99)
        assert result is None
