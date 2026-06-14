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
        self._modified_tasks = {}

        self.setWindowTitle(f"编辑任务 - {game_name}")
        self.resize(420, 520)
        self.setStyleSheet("QDialog { background: #18181b; }")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        header = QLabel(f"  {game_name} - 任务设置")
        header.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #f4f4f5;")
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

        # Buttons
        btn_row = QHBoxLayout()
        save_btn = QPushButton(" 保存")
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
        cb.setStyleSheet("""
            QCheckBox { color: #a1a1aa; font-size: 13px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border: 2px solid #3f3f46;
                border-radius: 4px; background: #09090b;
            }
            QCheckBox::indicator:checked {
                background: #6366f1; border-color: #6366f1;
            }
        """)
        cb.toggled.connect(lambda checked, t=task: self._on_toggle(t.task_id, checked))
        row_layout.addWidget(cb, stretch=1)

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
