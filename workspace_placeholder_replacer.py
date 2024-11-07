import typing


class WorkspacePlaceholderReplacer:
    """
    VSCodeのワークスペースファイル内のプレースホルダーを置き換えるクラス。

    属性
    ----------
    input_file_path : str
        入力となるcode-workspaceファイルのパス。
    output_file_path : str
        出力先のcode-workspaceファイルのパス。
    replacements : dict
        プレースホルダーと実際のパスの対応辞書。

    メソッド
    -------
    read_file() -> str
        入力ファイルを読み込み、その内容を文字列として返します。
    replace_placeholders(content: str) -> str
        コンテンツ内のプレースホルダーを実際のパスに置き換えます。
    write_file(content: str) -> None
        置き換えたコンテンツを出力ファイルに書き込みます。
    process() -> None
        読み込み、置き換え、書き込みの操作を順に実行します。
    """

    def __init__(
        self,
        input_file_path: str,
        output_file_path: str,
        replacements: typing.Dict[str, str],
    ) -> None:
        """
        WorkspacePlaceholderReplacerオブジェクトのすべての必要な属性を構築します。

        引数
        ----------
        input_file_path : str
            入力となるcode-workspaceファイルのパス。
        output_file_path : str
            出力先のcode-workspaceファイルのパス。
        replacements : dict
            プレースホルダーと実際のパスの対応辞書。
        """
        self.input_file_path = input_file_path
        self.output_file_path = output_file_path
        self.replacements = replacements

    def read_file(self) -> str:
        """
        入力ファイルを読み込み、その内容を文字列として返します。

        戻り値
        -------
        str
            入力ファイルの内容。
        """
        with open(self.input_file_path, "r", encoding="utf-8") as file:
            return file.read()

    def replace_placeholders(self, content: str) -> str:
        """
        コンテンツ内のプレースホルダーを実際のパスに置き換えます。

        引数
        ----------
        content : str
            入力ファイルの内容。

        戻り値
        -------
        str
            プレースホルダーが実際のパスに置き換えられた内容。
        """
        for placeholder, actual_path in self.replacements.items():
            content = content.replace(placeholder, actual_path)
        return content

    def write_file(self, content: str) -> None:
        """
        置き換えたコンテンツを出力ファイルに書き込みます。

        引数
        ----------
        content : str
            プレースホルダーが実際のパスに置き換えられた内容。
        """
        with open(self.output_file_path, "w", encoding="utf-8") as file:
            file.write(content)

    def process(self) -> None:
        """
        読み込み、置き換え、書き込みの操作を順に実行します。
        """
        content = self.read_file()
        updated_content = self.replace_placeholders(content)
        self.write_file(updated_content)
