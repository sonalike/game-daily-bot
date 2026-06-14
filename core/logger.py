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

    def close(self):
        """关闭并移除所有 handler，释放文件句柄"""
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)
