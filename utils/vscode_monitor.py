import configparser

import pygetwindow as gw

from .path_resolver import resolve_path

CONFIG_FILE_PATH = "config.ini"

config = configparser.ConfigParser()
config.read(resolve_path(CONFIG_FILE_PATH), "UTF-8")
vscode_monitor_config = config["VSCODE_MONITOR"]


class VSCodeMonitor:
    """VSCodeのウィンドウ監視を行うクラス"""

    @staticmethod
    def is_vscode_running() -> bool:
        """VSCodeのウィンドウが存在するかを確認"""
        for window in gw.getAllTitles():
            if "Visual Studio Code" in window:
                return True
        return False
