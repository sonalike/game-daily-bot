"""启动器主窗口"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import yaml
from pathlib import Path
from launcher.game_card import GameCard


class MainWindow(QMainWindow):
    """游戏日常助手 主窗口"""

    WINDOW_TITLE = "游戏日常助手"
    WINDOW_SIZE = (900, 600)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(*self.WINDOW_SIZE)

        self._games = {}
        self._runners = {}
        self._scheduler = None

        self._setup_ui()
        self._load_config()
        self._populate_game_list()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ── Left: Game list ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        header = QLabel("游戏列表")
        header.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #f4f4f5; padding: 4px 0;")
        left_layout.addWidget(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.game_list_widget = QWidget()
        self.game_list_layout = QVBoxLayout(self.game_list_widget)
        self.game_list_layout.setSpacing(6)
        self.game_list_layout.addStretch()
        self.scroll_area.setWidget(self.game_list_widget)
        left_layout.addWidget(self.scroll_area)

        self.stats_label = QLabel("共 0 款游戏")
        self.stats_label.setStyleSheet("color: #71717a; font-size: 12px; padding: 4px 0;")
        left_layout.addWidget(self.stats_label)

        # Button bar
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        self.btn_start_all = QPushButton("全部开始")
        self.btn_start_all.setStyleSheet(self._btn_style("#16a34a"))
        self.btn_start_all.clicked.connect(self._on_start_all)
        btn_layout.addWidget(self.btn_start_all)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setStyleSheet(self._btn_style("#dc2626"))
        self.btn_stop.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.btn_stop)

        self.btn_settings = QPushButton("SET")
        self.btn_settings.setFixedWidth(40)
        self.btn_settings.setStyleSheet(self._btn_style("#334155"))
        self.btn_settings.clicked.connect(self._on_settings)
        btn_layout.addWidget(self.btn_settings)

        left_layout.addWidget(btn_row)
        main_layout.addWidget(left_panel, stretch=1)

        # ── Right: Log ──
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        log_header = QLabel("执行日志")
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
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"games": []}

    def log(self, message: str):
        self.log_output.append(message)

    # ── Button callbacks ──

    def _on_start_all(self):
        self.log("[系统] 开始执行所有游戏任务...")
        self.btn_start_all.setEnabled(False)

    def _on_stop(self):
        self.log("[系统] 停止执行")
        self.btn_start_all.setEnabled(True)

    def _on_settings(self):
        self.log("[系统] 打开设置...")

    def _populate_game_list(self):
        """从配置加载游戏卡片"""
        games = self.config.get("games", [])
        if not games:
            games = [
                {"name": "崩坏：星穹铁道", "tasks": 5},
                {"name": "异环", "tasks": 4},
                {"name": "明日方舟：终末地", "tasks": 4},
                {"name": "火影忍者", "tasks": 4},
            ]

        # Clear old cards
        while self.game_list_layout.count() > 1:
            item = self.game_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for game in games:
            card = GameCard(game["name"], game.get("tasks", 0))
            card.clicked.connect(self._on_game_clicked)
            card.double_clicked.connect(self._on_game_double_clicked)
            self.game_list_layout.insertWidget(
                self.game_list_layout.count() - 1, card
            )

        self.stats_label.setText(f"共 {len(games)} 款游戏")

    def _on_game_clicked(self, name: str):
        self.log(f"[系统] 选中: {name}")

    def _on_game_double_clicked(self, name: str):
        self.log(f"[系统] 双击: {name}（任务编辑器将在 Task 12 完成）")
