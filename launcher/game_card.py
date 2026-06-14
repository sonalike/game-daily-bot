"""游戏卡片组件"""
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout,
                              QLabel, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class GameCard(QFrame):
    """单个游戏卡片"""

    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)

    STYLES = {
        "running": """
            GameCard {
                background: #1f1f23;
                border: 1px solid #3b82f6;
                border-left: 3px solid #3b82f6;
                border-radius: 8px;
            }
        """,
        "queued": """
            GameCard {
                background: #1f1f23;
                border: 1px solid #2a2a2e;
                border-radius: 8px;
            }
        """,
        "done": """
            GameCard {
                background: #1f1f23;
                border: 1px solid #22c55e;
                border-left: 3px solid #22c55e;
                border-radius: 8px;
            }
        """,
    }

    _ICONS = {
        "崩坏：星穹铁道": "⭐",
        "异环": "🌀",
        "明日方舟：终末地": "🏭",
        "火影忍者": "🍥",
    }

    def __init__(self, game_name: str, task_count: int = 0, parent=None):
        super().__init__(parent)
        self.game_name = game_name
        self._status = "queued"
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Icon
        icon = QLabel(self._game_icon(game_name))
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: #18181b; border-radius: 10px; font-size: 18px;")
        layout.addWidget(icon)

        # Info
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

        # Status badge
        self.status_label = QLabel("排队")
        self.status_label.setStyleSheet("""
            color: #71717a; font-size: 10px; font-weight: 600;
            background: #27272a; padding: 4px 10px; border-radius: 10px;
        """)
        layout.addWidget(self.status_label)

        self.setStyleSheet(self.STYLES["queued"])

    def _game_icon(self, name: str) -> str:
        return self._ICONS.get(name, "🎮")

    def set_status(self, status: str):
        self._status = status
        self.setStyleSheet(self.STYLES.get(status, self.STYLES["queued"]))
        status_text = {"running": "执行中", "queued": "排队", "done": "已完成"}
        self.status_label.setText(status_text.get(status, status))

    def mousePressEvent(self, event):
        self.clicked.emit(self.game_name)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.game_name)
