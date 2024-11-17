import configparser
import glob
import os
import tkinter as tk
import tkinter.messagebox as tk_messagebox
import typing
from tkinter import ttk

import pyglet

from .path_resolver import resolve_path
from .upload_manager import UploadManager

CONFIG_FILE_PATH = "config.ini"

config = configparser.ConfigParser()
config.read(resolve_path(CONFIG_FILE_PATH), "UTF-8")
file_upload_selector_config = config["FILE_UPLOAD_SELECTOR"]


class ExcludePattern:
    """
    除外リストを管理するクラス。

    属性
    ----------
    file_path : str
        除外リストのファイルパス
    exclude_patterns : List[str]
        除外リストの項目を格納するリスト
    """

    def __init__(self, file_path: str) -> None:
        """
        コンストラクタ。指定されたファイルパスから除外リストを読み込む。

        引数
        ----------
        file_path : str
            除外リストのファイルパス
        """
        self.file_path = file_path
        self.exclude_patterns = self._load_exclude_patterns()

    def _load_exclude_patterns(self) -> typing.List[str]:
        """
        除外リストファイルを読み込み、リスト形式で返す。

        戻り値
        -------
        List[str]
            除外リストの各行を要素とするリスト
        """
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                return [line.strip() for line in file.readlines()]
        return []

    def is_excluded(self, path: str) -> bool:
        """
        指定されたパスが除外リストに含まれているかを判定する。

        引数
        ----------
        path : str
            チェックするパス

        戻り値
        -------
        bool
            パスが除外リストに含まれていればTrue、含まれていなければFalse
        """
        folder_and_files = path.split("\\")
        return any(exclude in folder_and_files for exclude in self.exclude_patterns)


class FileManager:
    """
    ディレクトリからファイルとフォルダを取得し、除外リストを考慮して整形するクラス。

    属性
    ----------
    directory_path : str
        ファイル検索の起点となるディレクトリパス
    exclude_patterns : ExcludeList
        除外リストのインスタンス
    """

    def __init__(self, directory_path: str, exclude_patterns: ExcludePattern) -> None:
        """
        コンストラクタ。指定されたディレクトリからファイルとフォルダのリストを生成。

        引数
        ----------
        directory_path : str
            ファイル検索の起点となるディレクトリパス
        exclude_list : ExcludeList
            除外リストを管理するインスタンス
        """

        self.directory_path = directory_path
        self.exclude_patterns = exclude_patterns

    def list_directory_contents(self) -> typing.List[str]:
        """
        ディレクトリ内のファイルとフォルダを除外リストを考慮して取得し、ディレクトリを先にソートして返す。

        戻り値
        -------
        List[str]
            除外リストを考慮したディレクトリとファイルのリスト。ディレクトリが先に表示される。
        """

        def is_subfile(item: str) -> bool:
            """ファイル判定用ヘルパー関数"""
            return "\\" in item or os.path.isdir(os.path.join(self.directory_path, item))

        # 除外リストに含まれないアイテムを取得し、パスを整形
        all_items = (file.removeprefix(self.directory_path + "\\") for file in glob.glob(self.directory_path + r"\**\*", recursive=True))
        filtered_items = [item for item in all_items if not self.exclude_patterns.is_excluded(item)]

        # ディレクトリとファイルに分けてソート
        subfiled_paths = sorted(item for item in filtered_items if is_subfile(item))
        non_subfiled_paths = sorted(item for item in filtered_items if item not in subfiled_paths)

        return subfiled_paths + non_subfiled_paths


class FileUploadBrowserApp:
    """
    アップロードファイル選択アプリケーションのGUIを構築するクラス。

    属性
    ----------
    root : tk.Tk
        メインウィンドウ
    file_manager : FileManager
        ファイル管理を行うインスタンス
    check_vars : dict
        チェックボックス状態を保持する変数辞書
    """

    def __init__(self, root: tk.Tk, file_manager: FileManager, upload_manager: "UploadManager") -> None:
        """
        コンストラクタ。アプリケーションウィンドウの設定とウィジェット生成を行う。

        引数
        ----------
        root : tk.Tk
            Tkinterのルートウィンドウ
        file_manager : FileManager
            ファイル管理を行うインスタンス
        """
        self.root = root
        self.file_manager = file_manager

        self.check_vars: dict[str, tk.BooleanVar] = {}
        self._configure_window()
        self._create_widgets()

        if not os.path.isdir(self.file_manager.directory_path):
            tk_messagebox.showerror(
                "ワークスペースフォルダエラー",
                f"ワークスペースフォルダが存在しません：{self.file_manager.directory_path}",
            )
            self.root.destroy()
            return

        if not os.path.isfile(self.file_manager.exclude_patterns.file_path):
            tk_messagebox.showerror(
                "除外リストファイルエラー",
                f"除外リストファイルが存在しません：{self.file_manager.exclude_patterns.file_path}",
            )
            self.root.destroy()
            return

        self._setup_check_change_event()
        self.upload_manager = upload_manager
        self.uploaded_files: set[str] = set()  # アップロード済みのファイルを保持するセット

    def _configure_window(self) -> None:
        """ウィンドウの基本設定を行う。"""
        self.root.title(file_upload_selector_config["WINDOW_TITLE"])
        self.root.geometry(f"{file_upload_selector_config["WINDOW_WIDTH"]}x{file_upload_selector_config["WINDOW_HEIGHT"]}")
        icon_path = resolve_path(file_upload_selector_config["ICON_FILE"])
        icon_photo = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(False, icon_photo)
        self.root.resizable(width=False, height=False)  # ウィンドウサイズを固定
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """ウィジェットを作成し、配置を行う。"""

        # フォント設定
        pyglet.options.win32_gdi_font = True
        bizter_font_path = resolve_path(file_upload_selector_config["BIZTER_FONT_FILE"])
        pyglet.font.add_file(bizter_font_path)

        bizter_font = (file_upload_selector_config["BIZTER_FONT_FAMILY"], file_upload_selector_config.getint("BIZTER_FONT_SIZE"))
        file_list_font = (file_upload_selector_config["FILE_LIST_FONT_FAMILY"], file_upload_selector_config.getint("FILE_LIST_FONT_SIZE"))

        tk.Label(self.root, text=file_upload_selector_config["INSTRUCTION_TEXT"], font=bizter_font, fg="black").grid(row=0, column=0, padx=10, pady=10)

        self.file_list_frame = ttk.Frame(self.root)
        self.file_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # メッセージ表示エリア
        self.message_label = tk.Label(self.root, text="", font=bizter_font, fg="green")
        self.message_label.grid(row=2, column=0, pady=(0, 10))

        # 進捗バー
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=3, column=0, pady=(0, 10), padx=10, sticky="ew")

        # ボタンフレーム
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=4, column=0, pady=(0, 10))

        # アップロードボタン
        self.upload_button = tk.Button(button_frame, text="アップロード", command=self._on_upload, width=15)
        self.upload_button.pack(side="left", padx=5)

        # 閉じるボタン
        self.close_button = tk.Button(button_frame, text="閉じる", command=self._on_close, width=15)
        self.close_button.pack(side="left", padx=5)

        self._populate_filtered_file_list(file_list_font)

    def _populate_filtered_file_list(self, font: typing.Tuple[str, int]) -> None:
        """
        ディレクトリとファイルのリストをスクロール可能なエリアに表示する。

        引数
        ----------
        font : Tuple[str, int]
            表示用のフォント設定
        """
        canvas = tk.Canvas(self.file_list_frame)
        scrollbar = ttk.Scrollbar(self.file_list_frame, orient="vertical", command=canvas.yview)

        style = ttk.Style()
        style.configure(
            "frame.TFrame",
            background=file_upload_selector_config["FRAME_BG_COLOR"],
        )
        scrollable_frame = ttk.Frame(canvas, borderwidth=10, relief="groove", style="frame.TFrame")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=file_upload_selector_config.getint("WINDOW_WIDTH") - 50)
        canvas.configure(yscrollcommand=scrollbar.set)

        # マウスホイールでスクロールできるように設定
        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"),
        )

        list_directory_contents = self.file_manager.list_directory_contents()

        if not list_directory_contents:
            tk_messagebox.showwarning("ファイル警告", f"ファイルが存在しません。終了します。")
            self.root.destroy()
            return

        for item in list_directory_contents:
            var = tk.BooleanVar(value=True)
            file_name = item.rsplit("\\")[-1]
            is_file = os.path.isfile(os.path.join(self.file_manager.directory_path, item))

            # ディレクトリの場合は名前の後ろに「/」を追加
            display_name = f"{file_name} /" if not is_file else file_name

            widget = tk.Checkbutton(
                scrollable_frame,
                text=display_name,
                variable=var,
                font=font,
                background=file_upload_selector_config["FRAME_BG_COLOR"],
            )
            widget.pack(anchor="w", padx=30 * item.count("\\"), pady=0)  # 行間を小さくするためにpadyを0に設定
            self.check_vars[item] = var

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _get_selected_files(self) -> typing.List[str]:
        """
        選択されたファイルのリストを返す。

        戻り値
        -------
        List[str]
            選択されたファイルのリスト
        """
        select_files_folders = [os.path.join(self.file_manager.directory_path, item) for item, var in self.check_vars.items() if var.get()]
        return [select_files_folder for select_files_folder in select_files_folders if os.path.isfile(select_files_folder)]

    def _on_close(self) -> None:
        """
        ウィンドウが閉じられたときの処理。選択されたファイルを空のリストに設定する。
        """
        if not self.uploaded_files:
            delete_confirmed = tk_messagebox.askokcancel(
                f"警告",
                "ファイルがアップロードされていません。このまま閉じるとファイルがすべて削除されますが、よろしいですか？",
            )
            if not delete_confirmed:
                return
        self.check_vars = {}
        self.root.destroy()

    def _on_upload(self):
        """アップロードボタンが押されたときの処理。"""
        self.progress_bar["value"] = 0
        self.message_label.config(text="")

        selected_items = self._get_selected_files()

        if selected_items:
            # ボタンを無効化してアップロード開始
            self.upload_button.config(state="disabled")
            self.message_label.config(text="アップロード中…", fg="blue")

            deleting_items = [item for item in self.uploaded_files if item not in selected_items]
            for item in deleting_items:
                self.upload_manager.delete_file(item)
                self.uploaded_files.remove(item)

            # アップロード済みのファイルを追加
            new_files = [item for item in selected_items if item not in self.uploaded_files]

            if new_files:
                self.upload_manager.upload_files(new_files)  # 一度にアップロードする

            self.root.after(500, self._update_progress)  # 0.5秒後から進捗を更新
        else:
            self.message_label.config(text="エラー：ファイルが選択されていません", fg="red")

    def _update_progress(self):
        """プログレスバーを更新する。"""
        progress = self.upload_manager.get_upload_progress()
        self.progress_bar["value"] = progress

        if progress < 0:
            self.message_label.config(text="アップロードをキャンセルしました", fg="red")
            self.upload_button.config(state="normal")  # アップロード完了後にボタンを再度有効にする
        elif progress < 100:
            self.root.after(1000, self._update_progress)  # 1秒ごとに進捗を更新
        else:
            self.message_label.config(text="アップロードが完了しました", fg="green")
            self.upload_button.config(state="normal")
            self.uploaded_files.update(self._get_selected_files())

    def _setup_check_change_event(self):
        """各チェックボックスの変化イベントに _on_check_change メソッドをセット"""
        for item, var in self.check_vars.items():
            var.trace("w", lambda *args, item=item: self._on_selection_change(item))

    def _on_selection_change(self, item: str):
        """
        フォルダのチェック状態が変化した場合、フォルダ内のアイテムも連動してチェックまたはアンチェックする。

        引数
        ----------
        item : str
            チェック状態が変更されたアイテム
        """
        is_checked = self.check_vars[item].get()

        # フォルダの場合のみ、フォルダ内のアイテムに連動
        if os.path.isdir(os.path.join(self.file_manager.directory_path, item)):  # フォルダ判定
            # フォルダ内の全アイテムのチェックを変更
            for sub_item in self.check_vars:
                if sub_item.startswith(f"{item}\\"):
                    self.check_vars[sub_item].set(is_checked)  # アップロード完了後にボタンを再度有効にする


def select_upload_files(src_dir_path: str, dst_folder_path: str, exclude_pattern_file_path: str) -> None:
    """
    ファイル選択ダイアログを表示し、選択されたファイルのリストを返す。

    引数
    ----------
    src_dir_path : str
        ファイル検索の起点となるディレクトリパス
    dst_folder_path : str
        アップロード先のフォルダパス
    exclude_pattern_file_path : str
        除外リストのファイルパス
    """
    root = tk.Tk()

    exclude_patterns = ExcludePattern(exclude_pattern_file_path)
    file_manager = FileManager(src_dir_path, exclude_patterns)
    upload_manager = UploadManager()

    upload_manager.set_src_dir(src_dir_path)
    upload_manager.set_dst_folder(dst_folder_path)

    FileUploadBrowserApp(root, file_manager, upload_manager)

    root.mainloop()


if __name__ == "__main__":
    EXCLUDE_LIST_FILE = "exclude_list.txt"  # 除外リストのファイルパス
    SOURCE_DIRECTORY_PATH = r"C:\Users\Roy\Desktop\swimmy_python"  # ディレクトリパス
    DST_FOLDER_PATH = r"C:\Users\Roy\Google ドライブ\エキスパート\A＿あああいあうあえあお"
    select_upload_files(SOURCE_DIRECTORY_PATH, DST_FOLDER_PATH, EXCLUDE_LIST_FILE)
