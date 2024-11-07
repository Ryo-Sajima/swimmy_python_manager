import configparser
import datetime
import os
import pathlib
import shutil
import threading
import time
import tkinter.messagebox as tk_messagebox
import typing

from path_resolver import resolve_path

CONFIG_FILE_PATH = "config.ini"

config = configparser.ConfigParser()
config.read(resolve_path(CONFIG_FILE_PATH), "UTF-8")
upload_manager_config = config["UPLOAD_MANAGER"]


class UploadManager:
    """
    ファイルのコピーと進捗状況を管理するクラス。

    メソッド
    -------
    set_src_dir(src_dir)
        コピー元のディレクトリパスを設定する。
    set_dst_folder(dst_folder)
        コピー先のフォルダパスを設定する。
    get_progress()
        現在の進捗状況を取得する。
    upload_files(file_list)
        指定されたファイルのリストをコピーし、進捗状況を監視する。
    delete_file(filename)
        `dst_folder` 内に存在し、変更済みの指定ファイルを削除する。
    """

    def __init__(self) -> None:
        """
        UploadManagerの初期化。空の進捗状況と状態管理のための辞書を作成する。
        """
        self._file_statuses = {}
        self._progress = 0
        self._lock = threading.Lock()  # スレッド間でのデータ保護用
        self._src_dir = ""
        self._src_files = []
        self._dst_folder = ""

    def set_src_dir(self, src_dir: str) -> None:
        """
        コピー元のディレクトリパスを設定する。

        引数
        ----------
        dst_folder : str
            コピー元のディレクトリパス。
        """

        self._src_dir = src_dir
        self._src_dir_obj = pathlib.Path(self._src_dir)

    def set_dst_folder(self, dst_folder: str) -> None:
        """
        コピー先のフォルダパスを設定する。

        引数
        ----------
        dst_folder : str
            コピー先のフォルダパス。
        """
        self._dst_folder = dst_folder
        self._dst_folder_obj = pathlib.Path(self._dst_folder)

    def _get_last_accessed(self, path: str) -> datetime.datetime:
        """
        WMICを使用してファイルのLastAccessed値を取得し、datetimeオブジェクトに変換する。

        引数
        ----------
        path : str
            ファイルパス。

        戻り値
        -------
        datetime
            LastAccessed値のdatetimeオブジェクト。
        """
        return datetime.datetime.fromtimestamp(os.path.getatime(path))

    def _check_last_accessed(self, dst_path: str, status: dict) -> None:
        """
        指定されたファイルのLastAccessedを取得し、変更状態を更新する。

        引数
        ----------
        dst_path : str
            ファイルのパス。
        status : dict
            ファイルの状態を表す辞書。
        """
        current_last_accessed = self._get_last_accessed(dst_path)
        if current_last_accessed is not None:
            access_time_diff: float = (current_last_accessed - status["initial"]).total_seconds()
            if upload_manager_config.getint("ACCESS_CHANGE_THRESHOLD") <= access_time_diff:
                with self._lock:  # 他のスレッドと競合しないようにロック
                    status["changed"] = True

    def _get_relative_path(self, path: str) -> str:
        """
        パスの相対パスを生成します。

        引数
        ----------
        path : str
            ファイルのパス。

        戻り値
        -------
        str
            生成された相対パス。
        """
        source_path_obj = pathlib.Path(path)

        return str(source_path_obj.relative_to(self._src_dir_obj))

    def _get_new_path(self, path: str) -> str:
        """
        ソースパスとソースディレクトリに基づいて新しいファイルパスを生成します。

        引数
        ----------
        source_path : str
            新しいパスを生成するソースファイルのパス。

        戻り値
        -------
        str
            生成された新しいファイルパス。
        """
        source_path_obj = pathlib.Path(path)

        return str(self._dst_folder_obj / source_path_obj.relative_to(self._src_dir_obj))

    def upload_files(self, file_list: typing.List[str]) -> None:
        """
        指定されたファイルのリストをコピーし、進捗状況を監視する。

        引数
        ----------
        file_list : list of str
            コピーしたいファイルのパスのリスト。
        """
        self._src_files = file_list
        self._total_files = len(file_list)
        self._progress = 0
        self._file_statuses.clear()
        threading.Thread(target=self._copy_files, daemon=True).start()

    def _copy_files(self) -> None:
        """
        ファイルを順次コピーし、コピー完了後にLastAccessedを取得する。
        """
        existing_files = [src_file for src_file in self._src_files if os.path.isfile(self._get_new_path(src_file))]
        if existing_files:
            already_existing_files_str = "\n・".join(map(self._get_relative_path, existing_files))
            overwrite_confirmed = tk_messagebox.askokcancel(f"警告", f"以下のファイルは既に存在します。上書きしますか？\n・{already_existing_files_str}")
            if overwrite_confirmed:
                for already_existing_file in existing_files:
                    os.remove(self._get_new_path(already_existing_file))
                time.sleep(upload_manager_config.getint("WAIT_TIME_AFTER_DELETE"))
            else:
                self._progress = -1
                return

        for src_file in self._src_files:
            new_path = self._get_new_path(src_file)
            new_dir_path = os.path.dirname(new_path)
            os.makedirs(new_dir_path, exist_ok=True)
            copied_file_path = shutil.copy2(src_file, new_dir_path)

            # コピー直後にLastAccessedを取得
            initial_last_accessed = self._get_last_accessed(copied_file_path)
            if initial_last_accessed:
                with self._lock:  # 他のスレッドと競合しないようにロック
                    self._file_statuses[copied_file_path] = {"initial": initial_last_accessed, "changed": False}
            else:
                print(f"Failed to retrieve LastAccessed for {copied_file_path}")

        threading.Thread(target=self._monitor_progress, daemon=True).start()

    def _monitor_progress(self) -> None:
        """
        進捗を1秒おきに監視する。
        """
        while True:
            with self._lock:
                completed_files_count = sum(1 for status in self._file_statuses.values() if status["changed"])
                self._progress = int((completed_files_count / self._total_files) * 100)

            if self._progress >= 100:
                break

            for dst_path, status in self._file_statuses.items():
                if not status["changed"]:
                    # 現在のLastAccessedを取得するためにスレッドを使用
                    threading.Thread(target=self._check_last_accessed, args=(dst_path, status), daemon=True).start()

            time.sleep(upload_manager_config.getint("MONITOR_INTERVAL"))

    def get_upload_progress(self) -> int:
        """
        現在の進捗状況を取得する。

        戻り値
        -------
        int
            現在の進捗状況（0から100の範囲）。
        """
        return self._progress

    def delete_file(self, path: str) -> None:
        """
        指定されたファイルを削除する。

        引数
        ----------
        filename : str
            削除するファイルのパス。`dst_folder` 内にあり、かつ `changed` 状態であることが必要。

        注意書き
        -----
        ファイルが `dst_folder` に存在しないか、`changed` 状態でない場合は何も行わず無視する。
        """
        file_path = self._get_new_path(path)

        with self._lock:
            try:
                os.remove(file_path)
                del self._file_statuses[file_path]  # 状態管理からも削除
            except (FileNotFoundError, KeyError):
                pass  # ファイルが存在しない場合は無視
