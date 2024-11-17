import ctypes
import ctypes.wintypes
import os
import pathlib
import shutil
import tkinter.messagebox as tk_messagebox
import typing

import win32con  # type: ignore

# Windows Shell API の定数
SHGFI_ICON = 0x000000100  # アイコンを取得するためのフラグ
SHGFI_OVERLAYINDEX = 0x000000040  # オーバーレイアイコンのインデックスを取得するためのフラグ


class SHFILEINFO(ctypes.Structure):
    """Windows Shell API からアイコンやファイル情報を取得するための構造体。

    属性
    ----------
    hIcon : HICON
        アイコンハンドル
    iIcon : int
        アイコンインデックス
    dw属性 : int
        ファイル属性情報
    szDisplayName : str
        表示名
    szTypeName : str
        タイプ名
    """

    _fields_ = [
        ("hIcon", ctypes.wintypes.HICON),
        ("iIcon", ctypes.c_int),
        ("dw属性", ctypes.c_ulong),
        ("szDisplayName", ctypes.wintypes.WCHAR * 260),
        ("szTypeName", ctypes.wintypes.WCHAR * 80),
    ]


class OverlayIconFetcher:
    """ファイルのオーバーレイアイコンインデックスを取得するためのクラス。

    メソッド
    -------
    get_overlay_index(file_path: str) -> int | None
        指定したファイルのオーバーレイアイコンインデックスを取得する。
    """

    def __init__(self) -> None:
        self._shell32 = ctypes.windll.shell32
        self._shfi = SHFILEINFO()

    def get_overlay_index(self, file_path: str) -> int | None:
        """指定したファイルパスのオーバーレイアイコンインデックスを取得します。

        引数
        ----------
        file_path : str
            オーバーレイアイコンのインデックスを取得したいファイルのパス。

        戻り値
        -------
        int | None
            オーバーレイアイコンのインデックス（0はオーバーレイなしを示します）。
            エラーが発生した場合は None を返します。
        """
        try:
            self._shell32.SHGetFileInfoW(file_path, win32con.FILE_ATTRIBUTE_NORMAL, ctypes.byref(self._shfi), ctypes.sizeof(self._shfi), SHGFI_ICON | SHGFI_OVERLAYINDEX)
            # iIcon の上位8ビットからオーバーレイインデックスを取得
            overlay_index = self._shfi.iIcon >> 24
            return overlay_index
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            return None


class UploadManager:
    """ファイルのアップロード進捗状況を管理するクラス。

    ファイルのオーバーレイアイコンインデックスの変化でファイルの状態を検知し、
    get_upload_progress が呼ばれた際に進捗状況を更新します。

    属性
    ----------
    _file_statuses : dict
        ファイルごとの初期オーバーレイインデックスと変更状態の辞書
    _progress : int
        現在のアップロード進捗（0-100%）
    _src_dir : str
        コピー元のディレクトリパス
    _dst_folder : str
        コピー先のフォルダパス

    メソッド
    -------
    set_src_dir(src_dir: str) -> None
        コピー元のディレクトリパスを設定する。
    set_dst_folder(dst_folder: str) -> None
        コピー先のフォルダパスを設定する。
    upload_files(file_list: list[str]) -> None
        指定されたファイルのリストをコピーし、初期状態を記録する。
    get_upload_progress() -> int
        現在の進捗状況を取得する。
    delete_file(path: str) -> None
        指定されたファイルを削除し、状態管理から削除する。
    """

    def __init__(self) -> None:
        """UploadManagerの初期化。

        空の進捗状況と状態管理用辞書を初期化します。
        """
        self._file_statuses: dict[str, dict[str, typing.Any]] = {}
        self._progress: int = 0
        self._src_dir: str = ""
        self._dst_folder: str = ""
        self._overlay_icon_fetcher = OverlayIconFetcher()

    def set_src_dir(self, src_dir: str) -> None:
        """コピー元のディレクトリパスを設定する。

        引数
        ----------
        src_dir : str
            コピー元のディレクトリパス。
        """
        self._src_dir = src_dir
        self._src_dir_obj = pathlib.Path(self._src_dir)

    def set_dst_folder(self, dst_folder: str) -> None:
        """コピー先のフォルダパスを設定する。

        引数
        ----------
        dst_folder : str
            コピー先のフォルダパス。
        """
        self._dst_folder = dst_folder
        self._dst_folder_obj = pathlib.Path(self._dst_folder)

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

    def upload_files(self, file_list: list[str]) -> None:
        """指定されたファイルリストをコピーし、初期オーバーレイインデックスを取得して記録する。

        引数
        ----------
        file_list : list of str
            コピーしたいファイルのパスのリスト。
        """
        self._progress = 0
        self._file_statuses.clear()
        self._src_files = file_list  # コピー元ファイルのリストを格納
        self._total_size = 0  # 全ファイルの総バイトサイズ
        self._completed_size = 0  # 完了したファイルのバイトサイズ

        existing_files = [src_file for src_file in self._src_files if os.path.isfile(self._get_new_path(src_file))]

        # 上書き確認と既存ファイル削除
        if existing_files:
            already_existing_files_str = "\n・".join(map(self._get_relative_path, existing_files))
            overwrite_confirmed = tk_messagebox.askokcancel("警告", f"以下のファイルは既に存在します。上書きしますか？\n・{already_existing_files_str}")
            if overwrite_confirmed:
                for already_existing_file in existing_files:
                    os.remove(self._get_new_path(already_existing_file))
            else:
                self._progress = -1
                return  # 上書きしない場合は処理を中断

        # ファイルをコピーして、初期オーバーレイアイコンインデックスを取得
        for src_file in self._src_files:
            new_path = self._get_new_path(src_file)
            new_dir_path = os.path.dirname(new_path)
            os.makedirs(new_dir_path, exist_ok=True)
            copied_file_path = shutil.copy2(src_file, new_path)

            # ファイルサイズを取得し、0バイトの場合は1バイトと見なす
            file_size = max(1, os.path.getsize(src_file))
            self._total_size += file_size

            # オーバーレイアイコンインデックスを取得し、ファイル状態を初期化
            initial_overlay_index = self._overlay_icon_fetcher.get_overlay_index(copied_file_path)
            if initial_overlay_index is not None:
                self._file_statuses[copied_file_path] = {
                    "initial_overlay": initial_overlay_index,
                    "changed": False,
                    "size": file_size,
                }
            else:
                print(f"Failed to retrieve overlay index for {copied_file_path}")

    def get_upload_progress(self) -> int:
        """現在の進捗状況を取得する。

        ファイルのオーバーレイアイコンインデックスを確認し、前回と異なる場合に進捗を更新します。

        戻り値
        -------
        int
            現在の進捗状況（0から100の範囲）。
        """
        self._completed_size = 0

        for file_path, status in self._file_statuses.items():
            current_overlay = self._overlay_icon_fetcher.get_overlay_index(file_path)
            # 初期オーバーレイと異なれば "changed" とする
            if current_overlay is not None and current_overlay != status["initial_overlay"]:
                status["changed"] = True

            if status["changed"]:
                self._completed_size += status["size"]

        if self._total_size > 0:
            self._progress = int((self._completed_size / self._total_size) * 100)

        return self._progress

    def delete_file(self, path: str) -> None:
        """指定されたファイルを削除し、状態管理から削除する。

        引数
        ----------
        path : str
            削除するファイルのパス。`dst_folder` 内に存在し、`changed` 状態であることが必要。

        注意
        -----
        ファイルが `dst_folder` に存在しないか、`changed` 状態でない場合は何も行わず無視する。
        """
        full_path = os.path.join(self._dst_folder, os.path.relpath(path, self._src_dir))

        if full_path in self._file_statuses and self._file_statuses[full_path]["changed"]:
            try:
                os.remove(full_path)
                del self._file_statuses[full_path]
            except FileNotFoundError:
                pass  # ファイルが存在しない場合は無視
