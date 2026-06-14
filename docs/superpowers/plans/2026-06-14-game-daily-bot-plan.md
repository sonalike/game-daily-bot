# 游戏日常任务自动执行程序 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于图像识别 + ADB 模拟点击的通用游戏日常任务自动执行框架，支持 MuMu 模拟器上运行的多款手游，配备 PyQt6 桌面启动器。

**Architecture:** 分层架构 — 设备抽象层（ADB/云游戏）→ 核心引擎（识别/任务/调度）→ 游戏适配器（每游戏一个 Python 包）→ PyQt6 桌面启动器。上层通过统一接口调用下层，不感知底层实现。

**Tech Stack:** Python 3.11+, OpenCV, PaddleOCR, PyQt6, pure-python-adb, PyYAML, loguru

---

## Phase 1: 项目骨架搭建

### Task 1: 创建项目结构和依赖

**Files:**
- Create: `requirements.txt`
- Create: `config.yaml` (global default)
- Create: `core/__init__.py`
- Create: `games/__init__.py`
- Create: `launcher/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: 创建 requirements.txt**

```txt
# 核心
opencv-python>=4.8
numpy>=1.24
pyyaml>=6.0

# ADB
pure-python-adb>=0.3

# OCR
paddleocr>=2.7

# GUI
PyQt6>=6.5

# 工具
schedule>=1.2
loguru>=0.7
pillow>=10.0
```

- [ ] **Step 2: 创建目录结构**

```bash
mkdir -p core games launcher/launcher/resources
```

- [ ] **Step 3: 创建全局默认配置 config.yaml**

```yaml
device:
  type: adb
  adb_host: 127.0.0.1
  adb_port: 7555

schedule:
  daily_time: "06:00"
  interval_tasks: []

execution:
  step_timeout: 30
  game_timeout: 1800
  max_retries: 3

paths:
  screenshot_dir: ./screenshots/
  log_dir: ./logs/

games: []
```

- [ ] **Step 4: 创建所有 `__init__.py` 文件（全部为空文件）**

```bash
touch core/__init__.py games/__init__.py launcher/__init__.py
```

- [ ] **Step 5: 创建 .gitignore**

```gitignore
__pycache__/
*.pyc
.superpowers/
screenshots/
logs/
*.log
.env
```

- [ ] **Step 6: 验证目录结构**

```bash
ls -R
```

- [ ] **Step 7: 安装依赖**

```bash
pip install -r requirements.txt
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: scaffold project structure"
```

---

## Phase 2: 核心引擎 — 设备抽象层

### Task 2: 设备抽象基类

**Files:**
- Create: `core/device.py`
- Test: `tests/core/test_device.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_device.py`**

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_device.py -v
```

Expected: FAIL — module not found

- [ ] **Step 3: 实现 `core/device.py`**

```python
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
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_device.py -v
```

Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_device.py core/device.py core/__init__.py
git commit -m "feat: add Device abstract base class"
```

### Task 3: AdbDevice 实现

**Files:**
- Modify: `core/device.py` (add AdbDevice class)
- Test: `tests/core/test_adb_device.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_adb_device.py`**

```python
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
        # 构造一个最小有效的 PNG 文件 (1x1 red pixel)
        import zlib
        def make_png(w, h, raw_data):
            # Minimal PNG builder for a small image
            def chunk(chunk_type, data):
                c = chunk_type + data
                crc = zlib.crc32(c) & 0xffffffff
                return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)
            sig = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            # IDAT
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
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_adb_device.py -v
```

Expected: FAIL — AdbDevice not defined

- [ ] **Step 3: 实现 AdbDevice 类（追加到 core/device.py）**

```python
import subprocess
import io


class AdbDevice(Device):
    """通过 ADB 连接 MuMu 模拟器"""

    def __init__(self, host: str = '127.0.0.1', port: int = 7555):
        self.host = host
        self.port = port
        self.serial = f'{host}:{port}'
        self._resolution = None

    def _adb(self, *args, timeout: int = 10) -> subprocess.CompletedProcess:
        """执行 ADB 命令"""
        cmd = ['adb', '-s', self.serial] + list(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def connect(self) -> bool:
        """连接设备"""
        result = subprocess.run(
            ['adb', 'connect', self.serial],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0

    def screenshot(self) -> np.ndarray:
        """通过 ADB 获取屏幕截图"""
        import numpy as np
        import cv2

        result = self._adb('exec-out', 'screencap', '-p')
        if result.returncode != 0:
            raise RuntimeError(f"截图失败: {result.stderr}")

        # 从二进制 PNG 数据解码
        img_array = np.frombuffer(result.stdout, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("截图解码失败")
        return img

    def tap(self, x: int, y: int):
        self._adb('shell', 'input', 'tap', str(x), str(y), timeout=5)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        self._adb('shell', 'input', 'swipe',
                  str(x1), str(y1), str(x2), str(y2), str(duration),
                  timeout=5)

    def get_resolution(self) -> tuple[int, int]:
        if self._resolution is not None:
            return self._resolution
        result = self._adb('shell', 'wm', 'size')
        # Output: "Physical size: 1920x1080"
        line = result.stdout.strip()
        size_str = line.split(':')[-1].strip()
        w, h = size_str.split('x')
        self._resolution = (int(w), int(h))
        return self._resolution
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_adb_device.py -v
```

Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_adb_device.py core/device.py
git commit -m "feat: add AdbDevice implementation"
```

---

## Phase 3: 核心引擎 — 日志模块

### Task 4: 日志模块

**Files:**
- Create: `core/logger.py`
- Test: `tests/core/test_logger.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_logger.py`**

```python
import pytest
import os
import tempfile
from core.logger import GameLogger


class TestGameLogger:
    @pytest.fixture
    def log_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_init_creates_game_logger(self, log_dir):
        logger = GameLogger("崩坏：星穹铁道", log_dir)
        assert logger.game_name == "崩坏：星穹铁道"

    def test_log_info_writes_file(self, log_dir):
        logger = GameLogger("test_game", log_dir)
        logger.info("签到完成")
        log_file = os.path.join(log_dir, "test_game.log")
        assert os.path.exists(log_file)
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "签到完成" in content

    def test_log_error(self, log_dir):
        logger = GameLogger("test_game", log_dir)
        logger.error("连接失败")
        log_file = os.path.join(log_dir, "test_game.log")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "ERROR" in content
        assert "连接失败" in content
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_logger.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `core/logger.py`**

```python
"""日志模块 — 每游戏独立日志文件"""
import os
import logging
from datetime import datetime


class GameLogger:
    """游戏日志器，写入独立文件和 stdout"""

    def __init__(self, game_name: str, log_dir: str = './logs'):
        self.game_name = game_name
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        self.logger = logging.getLogger(f'game.{game_name}')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # 文件 handler
        log_path = os.path.join(log_dir, f'{game_name}.log')
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.logger.addHandler(fh)

        # 控制台 handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        ))
        self.logger.addHandler(ch)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_logger.py -v
```

Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_logger.py core/logger.py
git commit -m "feat: add GameLogger module"
```

---

## Phase 4: 核心引擎 — 图像识别

### Task 5: Vision 引擎 — 模板匹配

**Files:**
- Create: `core/vision.py`
- Test: `tests/core/test_vision.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_vision.py`**

```python
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
        """创建 200x200 模拟游戏画面，含一个白色方块 '按钮'"""
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        # 画一个白色方块作为"按钮"
        img[80:100, 80:120] = (255, 255, 255)
        return img

    @pytest.fixture
    def template_path(self):
        """创建一个 20x40 白色方块模板"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            template = np.full((20, 40, 3), 255, dtype=np.uint8)
            cv2.imwrite(f.name, template)
            path = f.name
        yield path
        os.unlink(path)

    def test_find_returns_position(self, vision, sample_screen, template_path):
        """模板匹配应找到白色方块位置"""
        result = vision.find(template_path, sample_screen)
        assert result is not None
        x, y = result
        # 匹配点在模板中心附近
        assert 80 <= x <= 120
        assert 80 <= y <= 100

    def test_find_returns_none_when_no_match(self, vision):
        """不存在的模板应返回 None"""
        black_screen = np.zeros((200, 200, 3), dtype=np.uint8)
        # 创建一个全白模板
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            white = np.full((50, 50, 3), 255, dtype=np.uint8)
            cv2.imwrite(f.name, white)
            path = f.name
        result = vision.find(path, black_screen)
        os.unlink(path)
        assert result is None

    def test_exists(self, vision, sample_screen, template_path):
        assert vision.exists(template_path, sample_screen) is True

    def test_exists_false(self, vision):
        black_screen = np.zeros((200, 200, 3), dtype=np.uint8)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            white = np.full((50, 50, 3), 255, dtype=np.uint8)
            cv2.imwrite(f.name, white)
            path = f.name
        result = vision.exists(path, black_screen)
        os.unlink(path)
        assert result is False

    def test_find_with_threshold(self, vision, sample_screen, template_path):
        """阈值 0.99 不应匹配（不是完全一致）"""
        result = vision.find(template_path, sample_screen, threshold=0.99)
        assert result is None
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_vision.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `core/vision.py`**

```python
"""图像识别引擎 — 模板匹配 + OCR + 特征检测"""
import cv2
import numpy as np
import time
from pathlib import Path
from typing import Optional


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

    def find(self, template_path: str, screenshot: np.ndarray = None,
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

    def exists(self, template_path: str, screenshot: np.ndarray = None,
               threshold: float = 0.85) -> bool:
        """模板是否存在"""
        return self.find(template_path, screenshot, threshold) is not None

    def wait_for(self, screenshot_provider, template_path: str,
                 timeout: float = 10, interval: float = 0.5) -> Optional[tuple[int, int]]:
        """等待模板出现，超时返回 None"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            screenshot = screenshot_provider()
            pos = self.find(template_path, screenshot)
            if pos is not None:
                return pos
            time.sleep(interval)
        return None

    def wait_until_gone(self, screenshot_provider, template_path: str,
                        timeout: float = 30, interval: float = 0.5) -> bool:
        """等待模板消失，超时返回 False"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            screenshot = screenshot_provider()
            if not self.exists(template_path, screenshot):
                return True
            time.sleep(interval)
        return False
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_vision.py -v
```

Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_vision.py core/vision.py
git commit -m "feat: add Vision engine with template matching"
```

---

## Phase 5: 核心引擎 — 任务执行

### Task 6: 任务数据结构 + GameAdapter 基类

**Files:**
- Create: `core/task.py`
- Test: `tests/core/test_task.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_task.py`**

```python
import pytest
from core.task import Task, TaskResult, TaskStatus, GameAdapter


class TestTask:
    def test_task_creation(self):
        t = Task(name="签到", task_id="signin", priority=1)
        assert t.name == "签到"
        assert t.task_id == "signin"
        assert t.priority == 1
        assert t.enabled is True

    def test_task_disabled(self):
        t = Task(name="模拟宇宙", task_id="simu", enabled=False)
        assert t.enabled is False

    def test_task_params(self):
        t = Task(name="清体力", task_id="stamina", params={"target": "auto", "count": 5})
        assert t.params["target"] == "auto"
        assert t.params["count"] == 5

    def test_task_equality(self):
        t1 = Task(name="A", task_id="a")
        t2 = Task(name="A", task_id="a")
        assert t1 == t2

    def test_task_sort_by_priority(self):
        tasks = [
            Task(name="C", task_id="c", priority=3),
            Task(name="A", task_id="a", priority=1),
            Task(name="B", task_id="b", priority=2),
        ]
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        assert [t.task_id for t in sorted_tasks] == ["a", "b", "c"]


class TestTaskResult:
    def test_success_result(self):
        r = TaskResult.ok("签到完成")
        assert r.status == TaskStatus.OK
        assert r.message == "签到完成"

    def test_fail_result(self):
        r = TaskResult.fail("找不到签到按钮")
        assert r.status == TaskStatus.FAILED
        assert r.message == "找不到签到按钮"

    def test_skip_result(self):
        r = TaskResult.skip("今日已完成")
        assert r.status == TaskStatus.SKIPPED


class TestGameAdapter:
    def test_abstract_class(self):
        """验证 GameAdapter 是抽象类"""
        with pytest.raises(TypeError):
            GameAdapter(None, {})

    class FakeAdapter(GameAdapter):
        def launch_game(self):
            self._launched = True
        def get_tasks(self):
            return [Task(name="test", task_id="t1")]
        def run_task(self, task):
            return TaskResult.ok("done")

    def test_concrete_adapter(self):
        class FakeDevice:
            def screenshot(self): return None
            def tap(self, x, y): pass
            def swipe(self, x1, y1, x2, y2, d=300): pass
            def get_resolution(self): return (1920, 1080)
            def wait(self, s): pass

        adapter = self.FakeAdapter(FakeDevice(), {})
        adapter.launch_game()
        assert adapter._launched is True

        tasks = adapter.get_tasks()
        assert len(tasks) == 1
        assert tasks[0].name == "test"

        result = adapter.run_task(tasks[0])
        assert result.status == TaskStatus.OK
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_task.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `core/task.py`**

```python
"""任务系统 — 数据结构 + GameAdapter 基类"""
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, Optional


class TaskStatus(Enum):
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    status: TaskStatus
    message: str = ""
    detail: Any = None

    @classmethod
    def ok(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.OK, message=message)

    @classmethod
    def fail(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.FAILED, message=message)

    @classmethod
    def skip(cls, message: str = "") -> "TaskResult":
        return cls(status=TaskStatus.SKIPPED, message=message)


@dataclass
class Task:
    name: str
    task_id: str
    priority: int = 99
    enabled: bool = True
    params: dict = field(default_factory=dict)

    def __eq__(self, other):
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id

    def __hash__(self):
        return hash(self.task_id)


class GameAdapter(ABC):
    """游戏适配器基类"""

    def __init__(self, device, config: dict):
        self.device = device
        self.config = config

    @abstractmethod
    def launch_game(self):
        """启动游戏到主界面"""
        ...

    @abstractmethod
    def get_tasks(self) -> list[Task]:
        """返回该游戏的所有任务列表（按优先级排序）"""
        ...

    @abstractmethod
    def run_task(self, task: Task) -> TaskResult:
        """执行单个任务"""
        ...
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_task.py -v
```

Expected: 8 PASS (需要也需要在 test_device.py 所在的 tests/core/ 目录加 __init__.py)

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_task.py core/task.py tests/core/__init__.py
git commit -m "feat: add Task data structures and GameAdapter base class"
```

---

## Phase 6: 核心引擎 — Runner + Scheduler

### Task 7: 任务执行器 (Runner)

**Files:**
- Create: `core/runner.py`
- Test: `tests/core/test_runner.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_runner.py`**

```python
import pytest
from unittest.mock import MagicMock
from core.task import Task, TaskResult, TaskStatus, GameAdapter
from core.runner import TaskRunner


class MockDevice:
    def screenshot(self): return None
    def tap(self, x, y): pass
    def swipe(self, x1, y1, x2, y2, d=300): pass
    def get_resolution(self): return (1920, 1080)
    def wait(self, s): pass


class MockAdapter(GameAdapter):
    def launch_game(self):
        self._launched = True
    def get_tasks(self):
        return [
            Task(name="签到", task_id="s1", priority=1),
            Task(name="清体力", task_id="s2", priority=2),
            Task(name="模拟宇宙", task_id="s3", priority=3, enabled=False),
        ]
    def run_task(self, task):
        if task.task_id == "s1":
            return TaskResult.ok("签到完成")
        elif task.task_id == "s2":
            return TaskResult.fail("体力不足")
        return TaskResult.skip("跳过")


class TestTaskRunner:
    @pytest.fixture
    def runner(self):
        device = MockDevice()
        adapter = MockAdapter(device, {})
        return TaskRunner(adapter, device, step_timeout=30, max_retries=2)

    def test_runner_init(self, runner):
        assert runner.adapter is not None
        assert runner.max_retries == 2

    def test_get_enabled_tasks(self, runner):
        tasks = runner._get_enabled_tasks()
        assert len(tasks) == 2
        assert tasks[0].task_id == "s1"
        assert tasks[1].task_id == "s2"
        # "s3" 是 disabled，不应出现

    def test_run_single_task(self, runner):
        task = Task(name="签到", task_id="s1")
        result = runner._run_single_task(task)
        assert result.status == TaskStatus.OK

    def test_run_all_tasks(self, runner):
        results = runner.run_all()
        assert len(results) == 2  # 2 enabled tasks
        assert results[0].status == TaskStatus.OK
        assert results[1].status == TaskStatus.FAILED

    def test_retry_on_failure(self, runner):
        """测试失败重试机制"""
        call_count = [0]

        class FlakyAdapter(MockAdapter):
            def run_task(self, task):
                call_count[0] += 1
                if call_count[0] < 3:
                    return TaskResult.fail(f"尝试 {call_count[0]} 失败")
                return TaskResult.ok("第3次成功")

        adapter = FlakyAdapter(MockDevice(), {})
        runner = TaskRunner(adapter, MockDevice(), max_retries=3)
        results = runner.run_all()
        assert len(results) == 2
        # 第一个任务重试了2次，第3次成功
        assert results[0].status == TaskStatus.OK
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_runner.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `core/runner.py`**

```python
"""任务执行引擎 — 状态机 + 重试 + 超时保护"""
import time
import random
from core.task import Task, TaskResult, TaskStatus, GameAdapter
from core.logger import GameLogger


class TaskRunner:
    """任务执行器 — 按优先级顺序执行游戏任务"""

    def __init__(self, adapter: GameAdapter, device,
                 step_timeout: int = 30, max_retries: int = 3,
                 game_timeout: int = 1800, logger=None):
        self.adapter = adapter
        self.device = device
        self.step_timeout = step_timeout
        self.max_retries = max_retries
        self.game_timeout = game_timeout
        self.logger = logger or GameLogger(adapter.__class__.__name__)

    def _get_enabled_tasks(self) -> list[Task]:
        """获取启用的任务列表（按优先级排序）"""
        tasks = [t for t in self.adapter.get_tasks() if t.enabled]
        return sorted(tasks, key=lambda t: t.priority)

    def _human_delay(self, min_ms: int = 200, max_ms: int = 800):
        """随机延迟，模拟人类操作"""
        delay = random.uniform(min_ms, max_ms) / 1000.0
        self.device.wait(delay)

    def _run_single_task(self, task: Task) -> TaskResult:
        """执行单个任务（含重试逻辑）"""
        self.logger.info(f"开始执行: {task.name}")

        for attempt in range(1, self.max_retries + 1):
            if attempt > 1:
                self.logger.info(f"重试 {attempt}/{self.max_retries}: {task.name}")

            try:
                result = self.adapter.run_task(task)
                if result.status == TaskStatus.OK:
                    self.logger.info(f"✓ {task.name} 完成")
                    return result
                elif result.status == TaskStatus.SKIPPED:
                    self.logger.info(f"⊘ {task.name} 跳过: {result.message}")
                    return result
                else:
                    self.logger.warning(f"✗ {task.name} 失败 (尝试 {attempt}): {result.message}")
            except Exception as e:
                self.logger.error(f"✗ {task.name} 异常: {e}")

        self.logger.error(f"✗ {task.name} 失败，已达最大重试次数")
        return TaskResult.fail(f"重试 {self.max_retries} 次后仍失败")

    def run_all(self) -> list[TaskResult]:
        """执行所有启用的任务"""
        tasks = self._get_enabled_tasks()
        self.logger.info(f"共 {len(tasks)} 个任务待执行")

        results = []
        start_time = time.time()

        for task in tasks:
            # 全局超时检查
            if time.time() - start_time > self.game_timeout:
                self.logger.error(f"全局超时 ({self.game_timeout}s)，跳过剩余任务")
                results.append(TaskResult.skip(f"全局超时: {task.name}"))
                continue

            self._human_delay()
            result = self._run_single_task(task)
            results.append(result)

        elapsed = time.time() - start_time
        ok_count = sum(1 for r in results if r.status == TaskStatus.OK)
        self.logger.info(f"完成: {ok_count}/{len(tasks)}, 耗时 {elapsed:.0f}s")
        return results
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_runner.py -v
```

Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_runner.py core/runner.py
git commit -m "feat: add TaskRunner with retry and timeout"
```

### Task 8: 调度器

**Files:**
- Create: `core/scheduler.py`
- Test: `tests/core/test_scheduler.py`

- [ ] **Step 1: 写失败的测试 `tests/core/test_scheduler.py`**

```python
import pytest
from unittest.mock import MagicMock, patch
from core.scheduler import Scheduler, ScheduleConfig


class TestScheduleConfig:
    def test_default_config(self):
        cfg = ScheduleConfig()
        assert cfg.daily_time == "06:00"
        assert cfg.enabled is True

    def test_custom_config(self):
        cfg = ScheduleConfig(daily_time="08:00", enabled=False)
        assert cfg.daily_time == "08:00"
        assert cfg.enabled is False


class TestScheduler:
    @pytest.fixture
    def scheduler(self):
        return Scheduler()

    def test_init(self, scheduler):
        assert scheduler._running is False

    def test_add_game(self, scheduler):
        mock_runner = MagicMock()
        scheduler.add_game("hsr", mock_runner)
        assert "hsr" in scheduler._games
        assert scheduler._games["hsr"] == mock_runner

    def test_remove_game(self, scheduler):
        mock_runner = MagicMock()
        scheduler.add_game("hsr", mock_runner)
        scheduler.remove_game("hsr")
        assert "hsr" not in scheduler._games

    def test_get_games(self, scheduler):
        scheduler.add_game("hsr", MagicMock())
        scheduler.add_game("yh", MagicMock())
        names = scheduler.get_game_names()
        assert set(names) == {"hsr", "yh"}

    def test_run_all_now(self, scheduler):
        mock_runner = MagicMock()
        mock_runner.run_all.return_value = []
        scheduler.add_game("hsr", mock_runner)
        results = scheduler.run_all_now()
        assert "hsr" in results
        mock_runner.run_all.assert_called_once()

    def test_run_single_game(self, scheduler):
        mock_hsr = MagicMock()
        mock_hsr.run_all.return_value = []
        mock_yh = MagicMock()
        scheduler.add_game("hsr", mock_hsr)
        scheduler.add_game("yh", mock_yh)
        results = scheduler.run_game_now("hsr")
        assert len(results) == 1
        mock_hsr.run_all.assert_called_once()
        mock_yh.run_all.assert_not_called()
```

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/core/test_scheduler.py -v
```

Expected: FAIL

- [ ] **Step 3: 实现 `core/scheduler.py`**

```python
"""调度器 — 定时/间隔/手动执行游戏任务"""
from dataclasses import dataclass, field
from typing import Optional
from core.task import TaskResult
from core.logger import GameLogger


@dataclass
class ScheduleConfig:
    daily_time: str = "06:00"
    enabled: bool = True
    interval_minutes: int = 0  # 0 = disabled


class Scheduler:
    """任务调度器 — 管理多款游戏的执行"""

    def __init__(self):
        self._games: dict[str, object] = {}  # game_name -> TaskRunner
        self._running = False
        self._logger = GameLogger("Scheduler")

    def add_game(self, name: str, runner) -> None:
        """注册游戏执行器"""
        self._games[name] = runner

    def remove_game(self, name: str) -> None:
        """移除游戏"""
        self._games.pop(name, None)

    def get_game_names(self) -> list[str]:
        """获取所有注册的游戏名称"""
        return list(self._games.keys())

    def run_all_now(self) -> dict[str, list[TaskResult]]:
        """立即执行所有游戏的任务"""
        self._running = True
        all_results = {}
        self._logger.info("开始执行所有游戏任务...")

        for name, runner in self._games.items():
            self._logger.info(f"[{name}] 开始执行")
            try:
                results = runner.run_all()
                all_results[name] = results
            except Exception as e:
                self._logger.error(f"[{name}] 执行异常: {e}")
                all_results[name] = []

        self._running = False
        ok_count = sum(
            sum(1 for r in results if r.status.value == "ok")
            for results in all_results.values()
        )
        self._logger.info(f"全部完成，成功 {ok_count} 个任务")
        return all_results

    def run_game_now(self, name: str) -> list[TaskResult]:
        """立即执行指定游戏"""
        if name not in self._games:
            raise KeyError(f"未注册的游戏: {name}")
        runner = self._games[name]
        self._logger.info(f"[{name}] 手动执行")
        return runner.run_all()

    @property
    def is_running(self) -> bool:
        return self._running
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/core/test_scheduler.py -v
```

Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_scheduler.py core/scheduler.py
git commit -m "feat: add Scheduler for multi-game orchestration"
```

---

## Phase 7: 首个游戏适配器 — 星穹铁道

### Task 9: 创建星穹铁道游戏适配器骨架 + 配置

**Files:**
- Create: `games/hsr/__init__.py`
- Create: `games/hsr/adapter.py`
- Create: `games/hsr/config.yaml`
- Create: `games/hsr/assets/.gitkeep`
- Test: `tests/games/test_hsr_adapter.py`

- [ ] **Step 1: 创建 HSR 配置 `games/hsr/config.yaml`**

```yaml
game:
  name: "崩坏：星穹铁道"
  package: "com.miHoYo.hkrpg"
  activity: ".MainActivity"

tasks:
  signin:
    enabled: true
    priority: 1
    description: "每日签到"
  claim_mail:
    enabled: true
    priority: 2
    description: "领取邮件"
  dispatch:
    enabled: true
    priority: 3
    description: "派遣收菜"
    duration_hours: 20
  spend_stamina:
    enabled: true
    priority: 4
    description: "清空体力"
    target: "auto"
    use_items: true
  sim_universe:
    enabled: false
    priority: 5
    description: "模拟宇宙"
    world: 9
```

- [ ] **Step 2: 写失败的测试 `tests/games/test_hsr_adapter.py`**

```python
import pytest
import yaml
import os
from pathlib import Path
from core.task import Task
from games.hsr.adapter import HsrAdapter


class MockDevice:
    def screenshot(self): return None
    def tap(self, x, y): pass
    def swipe(self, x1, y1, x2, y2, d=300): pass
    def get_resolution(self): return (1920, 1080)
    def wait(self, s): pass


class TestHsrAdapter:
    @pytest.fixture
    def config(self):
        config_path = Path(__file__).parent.parent.parent / "games" / "hsr" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def adapter(self, config):
        device = MockDevice()
        return HsrAdapter(device, config)

    def test_adapter_init(self, adapter):
        assert adapter is not None

    def test_get_tasks(self, adapter):
        tasks = adapter.get_tasks()
        assert len(tasks) >= 4
        task_ids = {t.task_id for t in tasks}
        assert "signin" in task_ids
        assert "dispatch" in task_ids
        assert "spend_stamina" in task_ids

    def test_tasks_sorted_by_priority(self, adapter):
        tasks = adapter.get_tasks()
        priorities = [t.priority for t in tasks]
        assert priorities == sorted(priorities)

    def test_disabled_task_not_in_list(self, adapter):
        tasks = adapter.get_tasks()
        # sim_universe is disabled in config
        task_ids = {t.task_id for t in tasks}
        assert "sim_universe" not in task_ids

    def test_launch_game(self, adapter):
        # 验证 launch_game 不抛异常（实际不连接设备）
        adapter.launch_game()

    def test_run_task_signin(self, adapter):
        task = Task(name="签到", task_id="signin", priority=1)
        result = adapter.run_task(task)
        # 没有真实设备，应返回跳过或失败（取决于实现选择）
        assert result is not None
```

- [ ] **Step 3: 运行测试确认失败**

```bash
pytest tests/games/test_hsr_adapter.py -v
```

Expected: FAIL — HsrAdapter not defined

- [ ] **Step 4: 实现 `games/hsr/adapter.py`**

```python
"""崩坏：星穹铁道 游戏适配器"""
import yaml
from pathlib import Path
from core.task import Task, TaskResult, GameAdapter


HERE = Path(__file__).parent
ASSETS_DIR = HERE / "assets"


class HsrAdapter(GameAdapter):
    """星穹铁道适配器"""

    GAME_PACKAGE = "com.miHoYo.hkrpg"
    GAME_ACTIVITY = ".MainActivity"

    def __init__(self, device, config: dict):
        super().__init__(device, config)
        self.assets = ASSETS_DIR

    def launch_game(self):
        """通过 ADB 启动游戏"""
        # 使用 am start 启动
        # 实际需要: adb shell am start -n com.miHoYo.hkrpg/.MainActivity
        pass

    def get_tasks(self) -> list[Task]:
        """从配置生成任务列表"""
        tasks_config = self.config.get("tasks", {})
        tasks = []

        for task_id, cfg in tasks_config.items():
            if not cfg.get("enabled", True):
                continue
            task = Task(
                name=cfg.get("description", task_id),
                task_id=task_id,
                priority=cfg.get("priority", 99),
                enabled=cfg.get("enabled", True),
                params={k: v for k, v in cfg.items()
                        if k not in ("enabled", "priority", "description")}
            )
            tasks.append(task)

        return sorted(tasks, key=lambda t: t.priority)

    def run_task(self, task: Task) -> TaskResult:
        """执行单个任务（骨架 — 实际逻辑在后续任务中实现）"""
        method_name = f"_do_{task.task_id}"
        method = getattr(self, method_name, None)

        if method is None:
            return TaskResult.skip(f"任务 {task.task_id} 未实现")

        return method(task)

    # ── 占位任务方法 ──

    def _do_signin(self, task: Task) -> TaskResult:
        """每日签到"""
        # TODO: 实现实际签到逻辑
        # 1. 等待主界面
        # 2. 点击签到入口
        # 3. 验证签到结果
        return TaskResult.skip("签到逻辑待实现（需素材）")

    def _do_claim_mail(self, task: Task) -> TaskResult:
        """领取邮件"""
        return TaskResult.skip("邮件领取待实现（需素材）")

    def _do_dispatch(self, task: Task) -> TaskResult:
        """派遣收菜"""
        return TaskResult.skip("派遣待实现（需素材）")

    def _do_spend_stamina(self, task: Task) -> TaskResult:
        """清空体力"""
        return TaskResult.skip("清体力待实现（需素材）")

    def _do_sim_universe(self, task: Task) -> TaskResult:
        """模拟宇宙"""
        return TaskResult.skip("模拟宇宙待实现（需素材）")
```

- [ ] **Step 5: 运行测试确认通过**

```bash
pytest tests/games/test_hsr_adapter.py -v
```

Expected: 6 PASS

- [ ] **Step 6: Commit**

```bash
git add tests/games/test_hsr_adapter.py games/hsr/ tests/games/__init__.py
git commit -m "feat: add HSR game adapter skeleton"
```

---

## Phase 8: 桌面启动器 (PyQt6)

### Task 10: 启动器主窗口骨架

**Files:**
- Create: `launcher/main_window.py`
- Create: `launcher/main.py` (启动入口)
- Test: `tests/launcher/test_main_window.py`

- [ ] **Step 1: 写启动器入口 `launcher/main.py`**

```python
"""游戏日常助手 — 桌面启动器入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from launcher.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 深色主题调色板
    from PyQt6.QtGui import QPalette, QColor
    from PyQt6.QtCore import Qt

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(24, 24, 27))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(244, 244, 245))
    palette.setColor(QPalette.ColorRole.Base, QColor(15, 15, 18))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(31, 31, 35))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(24, 24, 27))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(244, 244, 245))
    palette.setColor(QPalette.ColorRole.Text, QColor(244, 244, 245))
    palette.setColor(QPalette.ColorRole.Button, QColor(31, 31, 35))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(244, 244, 245))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(99, 102, 241))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(99, 102, 241))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 实现主窗口骨架 `launcher/main_window.py`**

```python
"""启动器主窗口"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import yaml
from pathlib import Path


class MainWindow(QMainWindow):
    """游戏日常助手 主窗口"""

    WINDOW_TITLE = "🎮 游戏日常助手"
    WINDOW_SIZE = (900, 600)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(*self.WINDOW_SIZE)

        # 数据
        self._games = {}       # game_name -> config
        self._runners = {}     # game_name -> TaskRunner
        self._scheduler = None

        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        """构建 UI 布局"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ── 左栏：游戏列表 ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # 标题
        header = QLabel("游戏列表")
        header.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #f4f4f5; padding: 4px 0;")
        left_layout.addWidget(header)

        # 滚动区域（游戏卡片容器）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.game_list_widget = QWidget()
        self.game_list_layout = QVBoxLayout(self.game_list_widget)
        self.game_list_layout.setSpacing(6)
        self.game_list_layout.addStretch()
        self.scroll_area.setWidget(self.game_list_widget)
        left_layout.addWidget(self.scroll_area)

        # 统计栏
        self.stats_label = QLabel("共 0 款游戏")
        self.stats_label.setStyleSheet("color: #71717a; font-size: 12px; padding: 4px 0;")
        left_layout.addWidget(self.stats_label)

        # 按钮栏
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        self.btn_start_all = QPushButton("▶ 全部开始")
        self.btn_start_all.setStyleSheet(self._btn_style("#16a34a"))
        self.btn_start_all.clicked.connect(self._on_start_all)
        btn_layout.addWidget(self.btn_start_all)

        self.btn_stop = QPushButton("■ 停止")
        self.btn_stop.setStyleSheet(self._btn_style("#dc2626"))
        self.btn_stop.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.btn_stop)

        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedWidth(40)
        self.btn_settings.setStyleSheet(self._btn_style("#334155"))
        self.btn_settings.clicked.connect(self._on_settings)
        btn_layout.addWidget(self.btn_settings)

        left_layout.addWidget(btn_row)
        main_layout.addWidget(left_panel, stretch=1)

        # ── 右栏：日志 ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        log_header = QLabel("📋 执行日志")
        log_header.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        log_header.setStyleSheet("color: #f4f4f5; padding: 4px 0;")
        right_layout.addWidget(log_header)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Cascadia Code", 10))
        self.log_output.setStyleSheet("""
            QTextEdit {
                background: #09090b;
                border: 1px solid #2a2a2e;
                border-radius: 8px;
                color: #a1a1aa;
                padding: 12px;
            }
        """)
        right_layout.addWidget(self.log_output)
        main_layout.addWidget(right_panel, stretch=1)

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """

    def _load_config(self):
        """加载全局配置"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"games": []}

    def log(self, message: str):
        """追加日志"""
        self.log_output.append(message)

    # ── 按钮回调（占位） ──

    def _on_start_all(self):
        self.log("[系统] 开始执行所有游戏任务...")
        self.btn_start_all.setEnabled(False)

    def _on_stop(self):
        self.log("[系统] 停止执行")
        self.btn_start_all.setEnabled(True)

    def _on_settings(self):
        self.log("[系统] 打开设置...")
```

- [ ] **Step 3: 运行启动器验证窗口能显示（手动测试）**

```bash
python launcher/main.py
```

Expected: 桌面窗口显示，深色主题，左栏游戏列表 + 右栏日志

- [ ] **Step 4: Commit**

```bash
git add launcher/main.py launcher/main_window.py launcher/__init__.py
git commit -m "feat: add PyQt6 launcher main window skeleton"
```

### Task 11: 游戏卡片组件 + 游戏列表集成

**Files:**
- Create: `launcher/game_card.py`
- Modify: `launcher/main_window.py` (集成卡片)

- [ ] **Step 1: 创建游戏卡片组件 `launcher/game_card.py`**

```python
"""游戏卡片组件"""
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout,
                              QLabel, QPushButton, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class GameCard(QFrame):
    """单个游戏卡片"""

    clicked = pyqtSignal(str)       # game_name
    start_clicked = pyqtSignal(str)
    stop_clicked = pyqtSignal(str)

    STYLES = {
        "running": """
            GameCard { background: #1f1f23; border: 1px solid #3b82f6;
                       border-left: 3px solid #3b82f6; border-radius: 8px; }
        """,
        "queued": """
            GameCard { background: #1f1f23; border: 1px solid #2a2a2e;
                       border-radius: 8px; }
        """,
        "done": """
            GameCard { background: #1f1f23; border: 1px solid #22c55e;
                       border-left: 3px solid #22c55e; border-radius: 8px; }
        """,
    }

    def __init__(self, game_name: str, task_count: int = 0, parent=None):
        super().__init__(parent)
        self.game_name = game_name
        self._status = "queued"
        self.setFixedHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # 图标
        icon = QLabel(self._game_icon(game_name))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: #18181b; border-radius: 10px; font-size: 18px;")
        layout.addWidget(icon)

        # 信息
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        self.name_label = QLabel(game_name)
        self.name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.name_label.setStyleSheet("color: #f4f4f5;")
        info_layout.addWidget(self.name_label)

        self.task_label = QLabel(f"任务: {task_count} 个")
        self.task_label.setStyleSheet("color: #71717a; font-size: 11px;")
        info_layout.addWidget(self.task_label)

        layout.addWidget(info, stretch=1)

        # 状态标签
        self.status_label = QLabel("排队")
        self.status_label.setStyleSheet("""
            color: #71717a; font-size: 10px; font-weight: 600;
            background: #27272a; padding: 4px 10px; border-radius: 10px;
        """)
        layout.addWidget(self.status_label)

        # 应用样式
        self.setStyleSheet(self.STYLES["queued"])
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _game_icon(self, name: str) -> str:
        icons = {
            "崩坏：星穹铁道": "⭐",
            "异环": "🌀",
            "明日方舟：终末地": "🏭",
            "火影忍者": "🍥",
        }
        return icons.get(name, "🎮")

    def set_status(self, status: str):
        """设置状态: running | queued | done"""
        self._status = status
        self.setStyleSheet(self.STYLES.get(status, self.STYLES["queued"]))
        status_text = {"running": "执行中", "queued": "排队", "done": "已完成"}
        self.status_label.setText(status_text.get(status, status))

    def mousePressEvent(self, event):
        self.clicked.emit(self.game_name)
```

- [ ] **Step 2: 更新主窗口集成卡片 `launcher/main_window.py`**

在 `__init__` 末尾添加 `self._populate_game_list()`，并添加方法：

```python
def _populate_game_list(self):
    """从配置加载游戏卡片"""
    games = self.config.get("games", [])
    if not games:
        # 测试用：添加示例游戏
        games = [
            {"name": "崩坏：星穹铁道", "tasks": 5},
            {"name": "异环", "tasks": 4},
            {"name": "明日方舟：终末地", "tasks": 4},
            {"name": "火影忍者", "tasks": 4},
        ]

    # 清除旧卡片
    while self.game_list_layout.count() > 1:  # 保留 stretch
        item = self.game_list_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    for game in games:
        card = GameCard(game["name"], game.get("tasks", 0))
        card.clicked.connect(self._on_game_clicked)
        self.game_list_layout.insertWidget(
            self.game_list_layout.count() - 1, card
        )

    self.stats_label.setText(f"共 {len(games)} 款游戏")


def _on_game_clicked(self, name: str):
    self.log(f"[系统] 选中游戏: {name}")
```

- [ ] **Step 3: 手动测试启动器**

```bash
python launcher/main.py
```

Expected: 左栏显示 4 张游戏卡片（带图标、名称、状态），右栏日志区

- [ ] **Step 4: Commit**

```bash
git add launcher/game_card.py launcher/main_window.py
git commit -m "feat: add GameCard component and game list"
```

### Task 12: 任务编辑器对话框

**Files:**
- Create: `launcher/task_editor.py`
- Modify: `launcher/main_window.py` (集成双击打开编辑器)

- [ ] **Step 1: 创建任务编辑器 `launcher/task_editor.py`**

```python
"""任务编辑器对话框"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                              QLabel, QCheckBox, QPushButton,
                              QScrollArea, QWidget, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.task import Task


class TaskEditor(QDialog):
    """游戏任务编辑对话框"""

    def __init__(self, game_name: str, tasks: list[Task], parent=None):
        super().__init__(parent)
        self.game_name = game_name
        self.tasks = tasks
        self._modified_tasks = {}  # task_id -> {enabled, priority}

        self.setWindowTitle(f"编辑任务 — {game_name}")
        self.resize(400, 500)
        self.setStyleSheet("""
            QDialog { background: #18181b; }
            QLabel { color: #f4f4f5; }
            QCheckBox { color: #a1a1aa; font-size: 13px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border: 2px solid #3f3f46;
                border-radius: 4px; background: #09090b;
            }
            QCheckBox::indicator:checked {
                background: #6366f1; border-color: #6366f1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel(f"🎮 {game_name} — 任务设置")
        header.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        task_widget = QWidget()
        self.task_layout = QVBoxLayout(task_widget)
        self.task_layout.setSpacing(6)

        for task in sorted(tasks, key=lambda t: t.priority):
            row = self._make_task_row(task)
            self.task_layout.addWidget(row)

        self.task_layout.addStretch()
        scroll.setWidget(task_widget)
        layout.addWidget(scroll)

        # 按钮
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 保存")
        save_btn.setStyleSheet(self._btn_style("#16a34a"))
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(self._btn_style("#334155"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _make_task_row(self, task: Task) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 4, 4, 4)
        row_layout.setSpacing(8)

        cb = QCheckBox(task.name)
        cb.setChecked(task.enabled)
        cb.toggled.connect(lambda checked, t=task: self._on_toggle(t.task_id, checked))
        row_layout.addWidget(cb, stretch=1)

        # 优先级设置
        priority_label = QLabel("优先级:")
        priority_label.setStyleSheet("color: #71717a; font-size: 11px;")
        row_layout.addWidget(priority_label)

        spin = QSpinBox()
        spin.setRange(1, 99)
        spin.setValue(task.priority)
        spin.setFixedWidth(60)
        spin.setStyleSheet("""
            QSpinBox {
                background: #09090b; border: 1px solid #2a2a2e;
                color: #f4f4f5; border-radius: 4px; padding: 2px 6px;
            }
        """)
        spin.valueChanged.connect(lambda v, t=task: self._on_priority(t.task_id, v))
        row_layout.addWidget(spin)

        return row

    def _on_toggle(self, task_id: str, enabled: bool):
        if task_id not in self._modified_tasks:
            self._modified_tasks[task_id] = {}
        self._modified_tasks[task_id]["enabled"] = enabled

    def _on_priority(self, task_id: str, priority: int):
        if task_id not in self._modified_tasks:
            self._modified_tasks[task_id] = {}
        self._modified_tasks[task_id]["priority"] = priority

    def get_changes(self) -> dict:
        return self._modified_tasks

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {color}; color: white; border: none;
                border-radius: 6px; padding: 8px 16px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """
```

- [ ] **Step 2: 在主窗口添加双击打开编辑器**

在 `launcher/main_window.py` 中修改 `_on_game_clicked`：

```python
def _on_game_clicked(self, name: str):
    self.log(f"[系统] 选中游戏: {name}")

def _on_game_double_clicked(self, name: str):
    """双击打开任务编辑器"""
    from launcher.task_editor import TaskEditor
    from core.task import Task

    # 创建示例任务列表（实际应从配置加载）
    sample_tasks = [
        Task(name="每日签到", task_id="signin", priority=1, enabled=True),
        Task(name="领取邮件", task_id="mail", priority=2, enabled=True),
        Task(name="派遣收菜", task_id="dispatch", priority=3, enabled=True,
             params={"duration": 20}),
        Task(name="清空体力", task_id="stamina", priority=4, enabled=True,
             params={"target": "auto"}),
        Task(name="模拟宇宙", task_id="simu", priority=5, enabled=False,
             params={"world": 9}),
    ]

    dialog = TaskEditor(name, sample_tasks, self)
    if dialog.exec() == TaskEditor.DialogCode.Accepted:
        changes = dialog.get_changes()
        self.log(f"[系统] 任务修改已保存: {len(changes)} 项变更")
```

并在 `_populate_game_list` 中绑定双击：

```python
card = GameCard(game["name"], game.get("tasks", 0))
card.clicked.connect(self._on_game_clicked)
card.mouseDoubleClickEvent = lambda e, n=game["name"]: self._on_game_double_clicked(n)
```

- [ ] **Step 3: 手动测试编辑器**

```bash
python launcher/main.py
```

双击游戏卡片 → 弹出任务编辑对话框 → 勾选/调整优先级 → 保存

- [ ] **Step 4: Commit**

```bash
git add launcher/task_editor.py launcher/main_window.py
git commit -m "feat: add TaskEditor dialog"
```

---

## Phase 9: 集成 & 入口

### Task 13: 程序主入口 — 连接所有模块

**Files:**
- Create: `main.py` (项目根目录)
- Modify: `config.yaml` (添加游戏列表)

- [ ] **Step 1: 更新全局配置 `config.yaml`（添加 games 列表）**

```yaml
device:
  type: adb
  adb_host: 127.0.0.1
  adb_port: 7555

schedule:
  daily_time: "06:00"
  interval_tasks: []

execution:
  step_timeout: 30
  game_timeout: 1800
  max_retries: 3

paths:
  screenshot_dir: ./screenshots/
  log_dir: ./logs/

games:
  - name: "崩坏：星穹铁道"
    config: games/hsr/config.yaml
    enabled: true
  - name: "异环"
    config: games/yihuan/config.yaml
    enabled: true
  - name: "明日方舟：终末地"
    config: games/zhongmodi/config.yaml
    enabled: true
  - name: "火影忍者"
    config: games/naruto/config.yaml
    enabled: true
```

- [ ] **Step 2: 创建项目根目录入口 `main.py`**

```python
"""游戏日常助手 — 入口点

用法:
    python main.py              # 启动桌面启动器
    python main.py --no-gui     # CLI 模式（直接执行所有任务）
    python main.py --game hsr   # 执行指定游戏
"""
import sys
import os
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="游戏日常助手")
    parser.add_argument("--no-gui", action="store_true", help="CLI 模式")
    parser.add_argument("--game", type=str, help="指定游戏名称")
    return parser.parse_args()


def run_cli(args):
    """CLI 模式 — 无 GUI 直接执行"""
    import yaml
    from core.device import AdbDevice
    from core.scheduler import Scheduler
    from games.hsr.adapter import HsrAdapter
    from core.runner import TaskRunner

    print("🚀 游戏日常助手 (CLI)")

    # 加载配置
    with open("config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 连接设备
    device_cfg = config["device"]
    device = AdbDevice(host=device_cfg["adb_host"], port=device_cfg["adb_port"])
    device.connect()
    print("✅ 设备已连接")

    # 创建调度器
    scheduler = Scheduler()
    exec_cfg = config["execution"]

    for game_cfg in config.get("games", []):
        if not game_cfg.get("enabled", True):
            continue
        name = game_cfg["name"]

        # 加载游戏配置
        game_config_path = game_cfg["config"]
        with open(game_config_path, 'r', encoding='utf-8') as f:
            game_config = yaml.safe_load(f)

        # 创建适配器（按名称路由）
        if "星穹铁道" in name:
            adapter = HsrAdapter(device, game_config)
        else:
            print(f"⚠️ {name}: 适配器未实现，跳过")
            continue

        runner = TaskRunner(
            adapter, device,
            step_timeout=exec_cfg["step_timeout"],
            max_retries=exec_cfg["max_retries"],
            game_timeout=exec_cfg["game_timeout"]
        )
        scheduler.add_game(name, runner)
        print(f"✅ {name} 已注册")

    # 执行
    if args.game:
        results = scheduler.run_game_now(args.game)
    else:
        results = scheduler.run_all_now()

    # 输出结果
    for name, task_results in results.items():
        ok = sum(1 for r in task_results if r.status.value == "ok")
        failed = sum(1 for r in task_results if r.status.value == "failed")
        skipped = sum(1 for r in task_results if r.status.value == "skipped")
        print(f"\n📊 {name}: ✓{ok} ✗{failed} ⊘{skipped}")

    print("\n✅ 完成")


def run_gui():
    """GUI 模式 — 启动桌面启动器"""
    from launcher.main import main
    main()


if __name__ == '__main__':
    args = parse_args()
    if args.no_gui:
        run_cli(args)
    else:
        run_gui()
```

- [ ] **Step 3: 手动测试 CLI 模式（无真实设备时预期输出设备连接失败，但不会崩溃）**

```bash
python main.py --no-gui
```

- [ ] **Step 4: 手动测试 GUI 模式**

```bash
python main.py
```

Expected: 启动器窗口打开，游戏卡片显示

- [ ] **Step 5: Commit**

```bash
git add main.py config.yaml
git commit -m "feat: add main entry point with CLI and GUI modes"
```

---

## Phase 10: 最终验证

### Task 14: 端到端测试 + 文档

**Files:**
- Create: `tests/test_integration.py`
- Modify: `README.md` (如果需要)

- [ ] **Step 1: 写集成测试 `tests/test_integration.py`**

```python
"""集成测试 — 验证完整流程"""
import pytest
import yaml
from pathlib import Path


class TestConfigIntegrity:
    """验证配置文件完整性"""

    def test_global_config_exists(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        assert config_path.exists(), "全局配置缺失"

    def test_global_config_valid(self):
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert "device" in config
        assert "schedule" in config
        assert "execution" in config
        assert "games" in config

    def test_hsr_config_exists(self):
        config_path = Path(__file__).parent.parent / "games" / "hsr" / "config.yaml"
        assert config_path.exists(), "星穹铁道配置缺失"

    def test_hsr_config_valid(self):
        config_path = Path(__file__).parent.parent / "games" / "hsr" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        assert "game" in config
        assert "tasks" in config
        assert "signin" in config["tasks"]


class TestCoreImports:
    """验证所有核心模块可导入"""

    def test_import_device(self):
        from core.device import Device, AdbDevice
        assert Device is not None
        assert AdbDevice is not None

    def test_import_vision(self):
        from core.vision import Vision
        assert Vision is not None

    def test_import_task(self):
        from core.task import Task, TaskResult, TaskStatus, GameAdapter
        assert Task is not None
        assert GameAdapter is not None

    def test_import_runner(self):
        from core.runner import TaskRunner
        assert TaskRunner is not None

    def test_import_scheduler(self):
        from core.scheduler import Scheduler
        assert Scheduler is not None

    def test_import_hsr(self):
        from games.hsr.adapter import HsrAdapter
        assert HsrAdapter is not None
```

- [ ] **Step 2: 运行全部测试**

```bash
pytest tests/ -v
```

Expected: 所有测试 PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests"
```

---

## 实现顺序总结

| Phase | 内容 | 预计耗时 |
|-------|------|----------|
| 1 | 项目骨架搭建 | 5 min |
| 2 | Device 抽象 + AdbDevice | 20 min |
| 3 | 日志模块 | 10 min |
| 4 | Vision 引擎 | 20 min |
| 5 | Task + GameAdapter 基类 | 15 min |
| 6 | Runner + Scheduler | 25 min |
| 7 | HSR 适配器骨架 | 15 min |
| 8 | PyQt6 启动器 | 40 min |
| 9 | 集成 + 入口 | 15 min |
| 10 | 最终验证 | 10 min |
| **总计** | | **~3 小时** |

## 后续扩展（本计划之外）

- HSR 实际任务逻辑（需截取游戏素材）
- 异环/终末地/火影 适配器
- 云游戏 CloudDevice
- 定时调度（schedule 库集成）
- 打包 .exe（PyInstaller）
- 多开模拟器支持
