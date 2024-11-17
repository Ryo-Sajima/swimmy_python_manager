import pygetwindow as gw


class VSCodeMonitor:
    """VSCodeのウィンドウ監視を行うクラス"""

    @staticmethod
    def is_vscode_running() -> bool:
        """VSCodeのウィンドウが存在するかを確認"""
        for window in gw.getAllTitles():
            if "Visual Studio Code" in window:
                return True
        return False
