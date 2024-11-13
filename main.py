import configparser
import datetime
import os
import sys
import tkinter.messagebox as tk_messagebox

from send2trash import send2trash

from utils.file_upload_selector import select_upload_files
from utils.folder_selector import select_folder
from utils.path_resolver import resolve_path
from utils.vscode_monitor import VSCodeMonitor
from utils.vscode_runner import VSCodeRunner
from utils.workspace_placeholder_replacer import WorkspacePlaceholderReplacer

CONFIG_FILE_PATH = "config.ini"


def main() -> int:
    if VSCodeMonitor.is_vscode_running():
        tk_messagebox.showerror("エラー", "別のVSCodeウィンドウが開かれているため、本ソフトウェアをご使用いただけません。\n先にすべてのVSCodeウィンドウを閉じてください。")
        return 1

    config = configparser.ConfigParser()
    config.read(resolve_path(CONFIG_FILE_PATH), "UTF-8")
    main_config = config["MAIN"]

    drive_path_resolved = resolve_path(main_config["DRIVE_PATH"])
    selected_folder = select_folder(drive_path_resolved)
    if selected_folder is None:
        return 0  # 選択されないので終了

    workspace_base_path_resolved = resolve_path(main_config["WORKSPACE_BASE_PATH"])
    workspace_path = os.path.join(workspace_base_path_resolved, selected_folder.replace("　", "_"))

    if os.path.isdir(workspace_path):
        restore_confirm = tk_messagebox.askquestion("ワークスペースの警告", "以前のワークスペースが残っています。復元しますか？")
        if not restore_confirm:
            send2trash(workspace_path)

    os.makedirs(workspace_path, exist_ok=True)

    selected_drive_path = os.path.join(drive_path_resolved, selected_folder)

    replacements = {
        "%DRIVE_PARENT_PATH%": drive_path_resolved.replace("\\", "\\\\"),
        "%DRIVE_PATH%": selected_drive_path.replace("\\", "\\\\"),
        "%WORKSPACE_PATH%": workspace_path.replace("\\", "\\\\"),
    }

    base_workspace_file_path_resolved = resolve_path(main_config["BASE_WORKSPACE_FILE_PATH"])
    workspace_file_path_resolved = resolve_path(main_config["WORKSPACE_FILE_PATH"])
    try:
        replacer = WorkspacePlaceholderReplacer(base_workspace_file_path_resolved, workspace_file_path_resolved, replacements)
        replacer.process()
    except Exception as e:
        tk_messagebox.showerror("ワークスペース生成エラー", f"ワークスペースを生成する際にエラーが発生しました: {e}")
        return 1

    # VSCodeを起動し、監視を開始
    vs_code_path_resolved = resolve_path(main_config["VS_CODE_PATH"])
    vs_code_runner = VSCodeRunner(vs_code_path_resolved, workspace_file_path_resolved)

    vs_code_runner.delete_last_history()
    try:
        vs_code_runner.run_and_wait()
    except Exception as e:
        tk_messagebox.showerror("ファイルエラー", f"ファイルを開く際にエラーが発生しました: {e}")
        return 1

    vs_code_runner.delete_workspace_storage()
    vs_code_runner.delete_last_history()

    drive_subfolder_name = datetime.date.strftime(datetime.date.today(), "%Y%m%d")

    drive_subfolder_path = os.path.join(selected_drive_path, drive_subfolder_name)

    upload_exclude_list_file_resolved = resolve_path(main_config["UPLOAD_EXCLUDE_LIST_FILE_PATH"])
    try:
        select_upload_files(workspace_path, drive_subfolder_path, upload_exclude_list_file_resolved)
    except Exception as e:
        tk_messagebox.showerror("アップロードエラー", f"ファイルのアップロード処理の際にエラーが発生しました: {e}")
        return 1

    send2trash(workspace_path)
    os.remove(workspace_file_path_resolved)

    return 0


if __name__ == "__main__":
    return_code = main()
    sys.exit(return_code)
