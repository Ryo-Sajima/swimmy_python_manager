import json
import os
import shutil
import subprocess

from .path_resolver import resolve_path

STORAGE_JSON_PATH = r"~\AppData\Roaming\Code\User\globalStorage\storage.json"
WORKSPACE_STORAGE_PATH = r"~\AppData\Roaming\Code\User\workspaceStorage"


class VSCodeRunner:
    """
    VSCodeを実行し、特定の出力を監視・取得するためのクラス。

    属性
    ----------
    _command : list[str]
        実行するVSCodeコマンドをリスト形式で保持。
    _workspace_id : Optional[str]
        検出されたworkspaceのID。
    """

    def __init__(self, vs_code_path: str, workspace_file_path: str) -> None:
        """
        VSCodeの実行パスとワークスペースファイルのパスでVSCodeRunnerを初期化。

        引数
        ----------
        vs_code_path : str
            VSCodeの実行ファイルへのパス。
        workspace_file_path : str
            ワークスペースファイルへのパス。
        """
        self._command = (vs_code_path, workspace_file_path, "--verbose", "-n")

    def run_and_wait(self) -> None:
        """
        コマンドを実行し、終了まで待つ。

        戻り値
        -------
        None
        """

        process = subprocess.Popen(self._command, creationflags=subprocess.CREATE_NO_WINDOW)

        process.wait()

    def delete_workspace_storage(self) -> None:
        """
        VSCodeの最後の履歴を削除する。

        戻り値
        -------
        None
        """

        storage_json_path_resolved = resolve_path(STORAGE_JSON_PATH)
        with open(storage_json_path_resolved) as f:
            storage_json_dict = json.load(f)

        workspace_id = storage_json_dict["windowsState"]["lastActiveWindow"]["workspaceIdentifier"]["id"]

        workspace_storage_path_resolved = resolve_path(WORKSPACE_STORAGE_PATH)
        id_workspace_storage_path = os.path.join(workspace_storage_path_resolved, workspace_id)
        shutil.rmtree(id_workspace_storage_path)

    def delete_last_history(self) -> None:
        """
        VSCodeの最後の履歴を削除する。

        戻り値
        -------
        None
        """

        storage_json_path_resolved = resolve_path(STORAGE_JSON_PATH)
        with open(storage_json_path_resolved) as f:
            storage_json_dict = json.load(f)

        storage_json_dict["windowsState"] = dict()

        with open(storage_json_path_resolved, "w") as f:
            json.dump(storage_json_dict, f, indent=4)


if __name__ == "__main__":
    # 使用例
    vs_code_path = "/path/to/code"  # 実際のVS Code実行ファイルのパスに置き換える
    workspace_file_path = "/path/to/workspace"  # 実際のワークスペースファイルのパスに置き換える
    runner = VSCodeRunner(vs_code_path, workspace_file_path)
    runner.run_and_wait()
    runner.delete_last_history()
