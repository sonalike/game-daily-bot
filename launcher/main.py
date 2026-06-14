"""游戏日常助手 — 桌面启动器入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from launcher.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

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
