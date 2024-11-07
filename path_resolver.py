import os
import sys


def resolve_path(path: str) -> str:
    """
    指定されたパスを絶対パスとして解決します。

    絶対パスならそのまま返し、相対パスならexeのディレクトリからの相対パスで解決します。また、`~`から始まる場合はユーザーホームからのパスを返します。

    引数
    ----------
    path : str
        解決したいパス文字列。

    戻り値
    -------
    str
        解決された絶対パス。

    例
    --------
    >>> resolve_path("~")
    '/home/user'
    >>> resolve_path("relative_path/to/file")
    '/current/working/directory/relative_path/to/file'
    """
    # `~`から始まる場合はホームディレクトリを展開
    if path.startswith("~"):
        return os.path.expanduser(path)

    # 絶対パスならそのまま返す
    if os.path.isabs(path):
        return path

    # 相対パスならこの関数が入っているファイルのディレクトリからのパスを返す
    current_file_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(current_file_dir, path)
