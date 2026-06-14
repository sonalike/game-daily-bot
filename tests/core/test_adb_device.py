import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from core.device import AdbDevice


class TestAdbDevice:
    @pytest.fixture
    def adb(self):
        with patch('core.device.subprocess') as mock_subprocess:
            device = AdbDevice(host='127.0.0.1', port=7555)
            device._subprocess = mock_subprocess
            yield device

    def test_init_defaults(self):
        d = AdbDevice()
        assert d.host == '127.0.0.1'
        assert d.port == 7555

    def test_init_custom(self):
        d = AdbDevice(host='192.168.1.1', port=5555)
        assert d.host == '192.168.1.1'
        assert d.port == 5555

    def test_connect(self, adb):
        adb._subprocess.run.return_value.returncode = 0
        adb.connect()
        adb._subprocess.run.assert_called_with(
            ['adb', 'connect', '127.0.0.1:7555'],
            capture_output=True, text=True, timeout=10
        )

    def test_tap(self, adb):
        adb._subprocess.run.return_value.returncode = 0
        adb.tap(500, 300)
        adb._subprocess.run.assert_called_with(
            ['adb', '-s', '127.0.0.1:7555', 'shell', 'input', 'tap', '500', '300'],
            capture_output=True, text=True, timeout=5
        )

    def test_swipe(self, adb):
        adb._subprocess.run.return_value.returncode = 0
        adb.swipe(100, 200, 300, 400, 500)
        adb._subprocess.run.assert_called_with(
            ['adb', '-s', '127.0.0.1:7555', 'shell', 'input', 'swipe',
             '100', '200', '300', '400', '500'],
            capture_output=True, text=True, timeout=5
        )

    def test_get_resolution(self, adb):
        adb._subprocess.run.return_value.stdout = 'Physical size: 1920x1080'
        adb._subprocess.run.return_value.returncode = 0
        w, h = adb.get_resolution()
        assert w == 1920
        assert h == 1080

    def test_screenshot_png_bytes(self, adb):
        import struct
        import zlib
        def make_png(w, h, raw_data):
            def chunk(chunk_type, data):
                c = chunk_type + data
                crc = zlib.crc32(c) & 0xffffffff
                return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)
            sig = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            raw_lines = b''
            for y in range(h):
                raw_lines += b'\x00' + raw_data[y * w * 3: (y + 1) * w * 3]
            compressed = zlib.compress(raw_lines)
            idat = chunk(b'IDAT', compressed)
            iend = chunk(b'IEND', b'')
            return sig + ihdr + idat + iend

        png_data = make_png(1, 1, b'\xff\x00\x00')  # 1x1 red pixel
        adb._subprocess.run.return_value.stdout = png_data
        adb._subprocess.run.return_value.returncode = 0
        img = adb.screenshot()
        assert isinstance(img, np.ndarray)
        assert img.shape == (1, 1, 3)
        # OpenCV BGR: red is (0, 0, 255)
        assert img[0, 0, 2] > 200  # red channel high
