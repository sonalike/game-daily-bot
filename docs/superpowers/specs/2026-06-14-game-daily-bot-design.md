# 游戏日常任务自动执行程序 — 设计文档

**日期:** 2026-06-14
**状态:** 设计中

---

## 1. 项目概述

### 1.1 目标

构建一个通用框架，自动执行国内网游（模拟器手游）的日常任务。用户上班/睡觉时自动完成签到、清体力、收菜等重复性操作。

### 1.2 核心需求

| 维度 | 决策 |
|------|------|
| 目标游戏 | 异环（完美世界）、崩坏：星穹铁道、明日方舟：终末地、火影忍者 |
| 运行平台 | MuMu 模拟器 (Android)，后期扩展云游戏 |
| 覆盖范围 | 全自动化 — 签到、副本、资源收集、基建管理等所有日常 |
| 技术方案 | 图像识别 + 模拟点击（不碰游戏进程，防封号） |
| 编程语言 | Python |
| 架构模式 | 脚本驱动框架 — 每游戏一个 Python 模块 |
| 启动器 | PyQt6 桌面 GUI |

### 1.3 非目标（本期不做）

- 云游戏支持（架构预留，后期实现）
- 社区插件市场
- 多语言国际化
- 移动端遥控

---

## 2. 架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────┐
│           桌面启动器 (PyQt6 GUI)          │  ← 用户交互层
├─────────────────────────────────────────┤
│           游戏适配器 (games/)             │  ← 每游戏的 Python 模块
├─────────────────────────────────────────┤
│  识别引擎    │  任务引擎    │  调度器      │  ← 核心引擎层
│  (vision.py) │  (runner.py) │ (scheduler) │
├─────────────────────────────────────────┤
│           设备抽象层 (device.py)          │  ← 统一设备接口
├──────────────┬──────────────────────────┤
│  AdbDevice   │  CloudDevice (后期)       │  ← 设备实现
│  (MuMu模拟器) │  (云游戏窗口)             │
└──────────────┴──────────────────────────┘
```

### 2.2 目录结构

```
daily-game-bot/
├── core/                       ← 核心引擎（与游戏无关）
│   ├── __init__.py
│   ├── device.py              ← 设备抽象基类 + AdbDevice 实现
│   ├── vision.py              ← 图像识别引擎
│   ├── runner.py              ← 任务执行引擎（状态机）
│   ├── scheduler.py           ← 定时调度器
│   └── logger.py              ← 日志模块
├── games/                      ← 游戏适配器
│   ├── hsr/                   ← 星穹铁道
│   │   ├── __init__.py
│   │   ├── adapter.py         ← 游戏适配器（继承 GameAdapter）
│   │   ├── assets/            ← 截图素材（按钮、图标等）
│   │   ├── tasks/             ← 各任务模块
│   │   │   ├── signin.py
│   │   │   ├── dispatch.py
│   │   │   ├── stamina.py
│   │   │   └── ...
│   │   └── config.yaml        ← 游戏配置
│   ├── yihuan/                ← 异环（完美世界）
│   ├── zhongmodi/             ← 终末地
│   └── naruto/                ← 火影忍者
├── launcher/                   ← 桌面启动器
│   ├── __init__.py
│   ├── main_window.py         ← 主窗口
│   ├── game_card.py           ← 游戏卡片组件
│   ├── log_panel.py           ← 日志面板
│   ├── task_editor.py         ← 任务编辑对话框
│   ├── settings_dialog.py     ← 设置对话框
│   └── resources/             ← GUI 资源（图标等）
├── config.yaml                 ← 全局配置
├── main.py                     ← 程序入口
└── requirements.txt
```

---

## 3. 核心模块设计

### 3.1 设备抽象层 (`core/device.py`)

**设计原则:** 上层代码只调用统一接口，不感知底层是 ADB 还是云游戏。

```python
class Device(ABC):
    """设备抽象基类"""

    @abstractmethod
    def screenshot(self) -> np.ndarray:
        """截取当前屏幕，返回 BGR numpy 数组"""
        ...

    @abstractmethod
    def tap(self, x: int, y: int):
        """点击坐标"""
        ...

    @abstractmethod
    def swipe(self, x1, y1, x2, y2, duration=300):
        """滑动"""
        ...

    @abstractmethod
    def get_resolution(self) -> tuple[int, int]:
        """返回 (宽, 高)"""
        ...

    def wait(self, seconds: float):
        """休眠"""
        time.sleep(seconds)
```

**AdbDevice（本期实现）:**
- 通过 `adb connect 127.0.0.1:7555` 连接 MuMu
- `screenshot()`: `adb exec-out screencap -p` → 二进制解析
- `tap()`: `adb shell input tap x y`
- `swipe()`: `adb shell input swipe x1 y1 x2 y2 duration`

**CloudDevice（后期实现）:**
- 截取云游戏窗口（Win32 PrintWindow / DXGI 桌面复制）
- 键鼠模拟（SendInput / PostMessage）

### 3.2 图像识别引擎 (`core/vision.py`)

三层识别策略，由框架自动选择：

| 层级 | 方法 | 技术 | 适用场景 | 占比 |
|------|------|------|----------|------|
| L1 | 模板匹配 | OpenCV `matchTemplate` | 固定按钮、图标、文字 | ~80% |
| L2 | OCR 文字识别 | PaddleOCR / Tesseract | 动态数值（体力、倒计时） | ~15% |
| L3 | 颜色/特征检测 | OpenCV 颜色范围、轮廓 | 加载画面、红点提示 | ~5% |

**核心 API:**
```python
def find(template_path: str, threshold=0.85) -> tuple[int,int] | None
def wait_for(template_path: str, timeout=10) -> tuple[int,int] | None
def exists(template_path: str) -> bool
def wait_until_gone(template_path: str, timeout=30) -> bool
def ocr_text(region: tuple) -> str
def find_red_dot(region: tuple) -> bool
```

**素材管理:**
- 每游戏 `assets/` 目录存放 PNG 截图
- 素材以功能命名：`signin_btn.png`、`stamina_full.png`、`claim_btn.png`
- 支持多分辨率素材（`signin_btn@1080p.png`），框架自动匹配

### 3.3 任务执行引擎 (`core/runner.py`)

每个任务按固定状态机流转：

```
开始 → 等待界面 → 识别目标 → 点击操作 → 验证结果
                                              ├── ✓ 成功 → 下一任务
                                              └── ✗ 失败 → 重试(最多3次)
                                                           ├── 成功 → 下一任务
                                                           └── 仍失败 → 记录错误 → 跳过
```

**异常处理:**
- 单步超时：每步操作 30s 未完成 → 重试
- 全局超时：单游戏整体超过 30min → 强制跳过，开始下一游戏
- 异常弹窗检测：每步后检测网络重连、更新提示、防沉迷弹窗，自动处理
- 崩溃恢复：检测游戏闪退 → 自动重启

**GameAdapter 基类:**
```python
class GameAdapter(ABC):
    """游戏适配器基类 — 每款游戏继承此类"""

    def __init__(self, device: Device, config: dict):
        self.device = device
        self.config = config

    @abstractmethod
    def launch_game(self): ...
    @abstractmethod
    def get_tasks(self) -> list[Task]: ...
    @abstractmethod
    def run_task(self, task: Task) -> TaskResult: ...
```

### 3.4 调度器 (`core/scheduler.py`)

**三种触发方式:**

| 方式 | 配置 | 说明 |
|------|------|------|
| 定时执行 | `cron: "0 6 * * *"` | 每天早上 6 点 |
| 间隔执行 | `interval: 4h` | 每 4 小时（基建收菜） |
| 手动触发 | GUI 按钮 | 立即执行 |

**执行策略:**
- 到时间自动启动模拟器 → 逐游戏串行执行 → 完成后写日志
- 同一时间只跑一款游戏（避免模拟器资源冲突）
- 支持多开模拟器（后期），每实例绑定不同游戏

### 3.5 配置体系

**全局配置 (`config.yaml`):**
```yaml
device:
  type: adb                    # adb | cloud
  adb_host: 127.0.0.1
  adb_port: 7555               # MuMu 默认 ADB 端口

schedule:
  daily_time: "06:00"          # 每日执行时间
  interval_tasks: []           # 间隔任务列表

execution:
  step_timeout: 30             # 单步超时(秒)
  game_timeout: 1800           # 单游戏总超时(秒)
  max_retries: 3               # 单步最大重试次数

paths:
  screenshot_dir: ./screenshots/
  log_dir: ./logs/
```

**游戏配置 (`games/xxx/config.yaml`):**
```yaml
game:
  name: "崩坏：星穹铁道"
  package: "com.miHoYo.hkrpg"
  activity: ".MainActivity"
  resolution: [1920, 1080]

tasks:
  signin:
    enabled: true
    priority: 1
  claim_mail:
    enabled: true
    priority: 2
  dispatch:
    enabled: true
    priority: 3
    duration: 20               # 派遣时长(小时)
  spend_stamina:
    enabled: true
    priority: 4
    target: "auto"             # auto | 副本ID
    use_items: true            # 是否使用体力药
  sim_universe:
    enabled: false             # 暂不执行
    priority: 5
    world: 9
```

---

## 4. 桌面启动器设计

### 4.1 技术选型

- **框架:** PyQt6（Windows 原生窗口，成熟稳定）
- **主题:** 深色主题，暗黑风格
- **布局:** 左侧游戏列表 + 右侧日志面板

### 4.2 功能清单

| 功能 | 说明 |
|------|------|
| 🎮 游戏列表 | 卡片式展示，显示状态和当前任务 |
| ▶️ 单游戏启停 | 每款游戏独立 开始/停止 按钮 |
| ▶️ 全部开始/停止 | 一键执行所有或停止所有 |
| 🔧 游戏设置 | 勾选任务、调参数、拖拽排序 |
| 📝 实时日志 | 滚动日志，按游戏过滤 |
| 📊 执行详情 | 选中游戏后显示任务进度和耗时 |
| ⏰ 定时设置 | 配置每日执行时间 |
| 📜 执行历史 | 查看历史执行记录 |

### 4.3 任务编辑

两种方式并存：

1. **YAML 配置文件** — 直接编辑 `config.yaml`，适合批量调整、首次配置
2. **GUI 任务编辑器** — 在启动器中勾选/拖拽/改参数，实时生效
   - 勾选开关任务
   - 拖拽排序优先级
   - 点击齿轮修改参数（数值、选项）
   - "添加自定义步骤"（原子操作拼接）

### 4.4 三层自定义能力

| 层级 | 操作 | 适用人群 |
|------|------|----------|
| 🎛️ 开关 + 调参 | 勾选任务、改数值 | 所有用户 |
| 🧩 原子操作拼接 | 拖拽组合内置步骤 | 进阶用户 |
| 🐍 Python 脚本 | 编写任意复杂逻辑 | 开发者 |

---

## 5. 游戏适配开发顺序

开发优先级按复杂度从低到高：

1. **崩坏：星穹铁道** — 首个适配，验证框架可行性。UI 规范、操作路径清晰。
2. **异环** — 完美世界新游，UI 可能变动频繁，需验证识别引擎鲁棒性。
3. **火影忍者** — 动作游戏，可能有战斗场景，需处理动态画面。
4. **明日方舟：终末地** — 基建系统复杂，任务逻辑最重。

---

## 6. 技术风险 & 缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 游戏更新改 UI | 素材失效，任务卡住 | 素材版本管理 + OCR 兜底 + 日志提示更新素材 |
| 反作弊检测 | 账号风险 | 只用图像识别+模拟点击，不碰进程/内存。添加随机延迟模拟人类操作 |
| 模拟器版本兼容 | ADB 连接失败 | 支持配置 ADB 端口，自动检测 MuMu 版本 |
| 动态加载/过场动画 | 识别超时 | 智能等待：检测画面变化趋于静止后才开始识别 |
| 多分辨率适配 | 素材不匹配 | 素材支持多分辨率版本，坐标按比例换算 |

---

## 7. 后续扩展（v2+）

- ☁️ CloudDevice 实现（网易云游戏、腾讯START）
- 📱 多开模拟器支持（同时跑多款游戏）
- 🔔 通知推送（企业微信/钉钉/Bark 通知执行结果）
- 📦 打包为单个 .exe（PyInstaller）
- 🌐 远程 Web 面板（手机查看状态）

---

## 8. 附录

### 8.1 依赖库

```
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
schedule>=1.2        # 定时调度
loguru>=0.7          # 日志
pillow>=10.0         # 图片处理
```

### 8.2 开发环境

- Python 3.11+
- Windows 11
- MuMu 模拟器 12
- ADB (随 MuMu 附带)
