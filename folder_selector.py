import configparser
import os
import tkinter as tk
import tkinter.font as tk_font
import tkinter.messagebox as tk_messagebox

import pyglet

from path_resolver import resolve_path

CONFIG_FILE_PATH = "config.ini"

config = configparser.ConfigParser()
config.read(resolve_path(CONFIG_FILE_PATH), "UTF-8")
folder_selector_config = config["FOLDER_SELECTOR"]


# 定数設定


class FolderLister:
    """指定されたディレクトリ内のフォルダーをリストするクラス

    属性:
        directory (str): フォルダーをリストするディレクトリのパス
    """

    def __init__(self, directory: str) -> None:
        """
        引数
        ----------
        directory : str
            フォルダーをリストするディレクトリのパス
        """
        self.directory = directory

    def list_folders(self) -> list[str]:
        """指定されたディレクトリ内のフォルダーのみをリストで返す

        戻り値
        -------
        list[str]
            フォルダー名のリスト
        """
        try:
            with os.scandir(self.directory) as entries:
                return sorted([entry.name for entry in entries if entry.is_dir()])
        except FileNotFoundError:
            tk_messagebox.showerror("エラー", f"ディレクトリ {self.directory} が見つかりません。")
            return []


class FolderSelectorUI:
    """フォルダー選択UIを管理するクラス

    属性:
        root (tk.Tk): Tkinterのルートウィンドウ
        folder_lister (FolderLister): フォルダーリストを管理するオブジェクト
        selected_folder (str | None): 選択されたフォルダー名
        font (tk_font.Font): 使用するフォント
    """

    def __init__(self, root: tk.Tk, folder_lister: FolderLister) -> None:
        """
        引数
        ----------
        root : tk.Tk
            Tkinterのルートウィンドウ
        folder_lister : FolderLister
            フォルダーリストを管理するオブジェクト
        """
        self.root = root
        self.folder_lister = folder_lister
        self.selected_folder = None

        pyglet.options["win32_gdi_font"] = True
        font_path = resolve_path(folder_selector_config["BIZTER_FONT_FILE"])
        pyglet.font.add_file(font_path)
        self.font = tk_font.Font(family=folder_selector_config["BIZTER_FONT_FAMILY"], size=folder_selector_config.getint("BIZTER_FONT_SIZE"))

        self._initialize_ui()

    def _initialize_ui(self) -> None:
        """UIコンポーネントを初期化"""
        self._configure_root()
        self._create_label()
        self._create_listbox_with_scrollbar()

    def _configure_root(self) -> None:
        """ルートウィンドウのプロパティを設定"""
        self.root.title(folder_selector_config["WINDOW_TITLE"])
        self._center_window(folder_selector_config.getint("WINDOW_WIDTH"), folder_selector_config.getint("WINDOW_HEIGHT"))
        self.root.resizable(False, False)
        icon_path = resolve_path(folder_selector_config["ICON_FILE"])
        icon_photo = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(False, icon_photo)

    def _create_label(self) -> None:
        """指示ラベルを作成"""
        label = tk.Label(self.root, text=folder_selector_config["INSTRUCTION_TEXT"], anchor="w", font=self.font)
        label.pack(fill="x", padx=20, pady=(20, 5))

    def _create_listbox_with_scrollbar(self) -> None:
        """ファイル選択用のListboxとスクロールバーを含むフレームを作成"""
        frame = tk.Frame(self.root)
        frame.pack(pady=20, padx=20)

        # スクロールバーとListboxの設定
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        folders = self.folder_lister.list_folders()
        self.folder_listbox = tk.Listbox(
            frame,
            listvariable=tk.StringVar(value=folders),
            height=20,
            width=20,
            font=self.font,
            cursor="hand2",
            yscrollcommand=scrollbar.set,
        )
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar.config(command=self.folder_listbox.yview)

        self.folder_listbox.bind("<<ListboxSelect>>", self.on_folder_selected)

    def _center_window(self, width: int, height: int) -> None:
        """ウィンドウを画面の中央に配置

        引数
        ----------
        width : int
            ウィンドウの幅
        height : int
            ウィンドウの高さ
        """
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def on_folder_selected(self, event) -> None:
        """Listboxからファイルが選択されたときの処理"""
        self.selected_folder = self._get_selected_folder()
        if self.selected_folder:
            self.root.after(100, self.root.destroy)  # ウィンドウを閉じる

    def _get_selected_folder(self) -> str | None:
        """Listboxで選択されたファイルを取得

        戻り値
        -------
        str | None
            選択されたフォルダー名、またはNone
        """
        try:
            selected_index = self.folder_listbox.curselection()
            if selected_index:
                return self.folder_listbox.get(selected_index)
        except Exception as e:
            tk_messagebox.showerror("エラー", f"ファイルの選択中にエラーが発生しました: {e}")
        return None


class FolderSelectorApp:
    """フォルダー選択アプリケーションのメインクラス

    属性:
        directory (str): フォルダーをリストするディレクトリのパス
    """

    def __init__(self, directory: str) -> None:
        """
        引数
        ----------
        directory : str
            フォルダーをリストするディレクトリのパス
        """
        self.directory = directory

    def run(self) -> str | None:
        """フォルダー選択アプリケーションを実行し、選択されたフォルダーを返す

        戻り値
        -------
        str | None
            選択されたフォルダー名、またはNone
        """
        root = tk.Tk()
        folder_lister = FolderLister(self.directory)
        ui = FolderSelectorUI(root, folder_lister)
        root.mainloop()
        return ui.selected_folder


def select_folder(directory: str) -> str | None:
    """フォルダー選択アプリケーションを起動し、選択されたフォルダーを返す

    引数
    ----------
    directory : str
        フォルダーをリストするディレクトリのパス

    戻り値
    -------
    str | None
        選択されたフォルダー名、またはNone
    """
    app = FolderSelectorApp(directory)
    return app.run()
