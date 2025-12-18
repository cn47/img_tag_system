from typing import BinaryIO, Protocol, TextIO, runtime_checkable


@runtime_checkable
class StoragePath(Protocol):
    """ストレージパス"""

    def __str__(self) -> str: ...
    def __truediv__(self, key: str) -> "StoragePath":
        """パスを結合する (path / 'filename' の形式)"""
        ...

    # --- propreties ---
    @property
    def name(self) -> str: ...
    @property
    def suffix(self) -> str: ...
    @property
    def parent(self) -> "StoragePath": ...
    @property
    def as_uri(self) -> str: ...

    # --- query operations(side-effect free) ---
    def exists(self) -> bool: ...
    def is_file(self) -> bool: ...
    def is_dir(self) -> bool: ...

    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> BinaryIO | TextIO:
        """ファイルを開く（コンテキストマネージャーとして使用可能）

        Args:
            mode(str): ファイルを開くモード（"r", "w", "rb", "wb"など）
            buffering(int): バッファリングポリシー
            encoding(str | None): テキストモードでのエンコーディング
            errors(str | None): エンコーディングエラーの処理方法
            newline(str | None): テキストモードでの改行処理

        Returns:
            BinaryIO | TextIO: ファイルオブジェクト（コンテキストマネージャー）

        Examples:
            >>> with storage_path.open("rb") as f:
            ...     data = f.read()
            >>> with storage_path.open("r", encoding="utf-8") as f:
            ...     text = f.read()
        """
        ...

    def get_size(self) -> int:
        """ファイルサイズ（バイト数）を取得する

        Returns:
            int: ファイルサイズ（バイト数）

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        ...

    def list_files(self, recursive: bool = False) -> list["StoragePath"]:
        """ファイルを走査してパスのリストを返す

        Args:
            recursive(bool): 再帰的に走査するかどうか。True の場合はディレクトリも再帰的に走査する。
                False の場合はディレクトリは走査しない。
                デフォルトは False。

        Returns:
            list[StoragePath]: ファイルのパスリスト
        """
        ...

    # --- command operations(side-effect) ---
    def copy(self, destination: "StoragePath", overwrite: bool = False) -> "StoragePath":
        """ファイルをコピーする

        Args:
            destination(StoragePath): コピー先のパス
            overwrite(bool): 上書きするかどうか。デフォルトは False。

        Returns:
            StoragePath: コピー先のパス
        """
        ...

    def move(self, destination: "StoragePath", overwrite: bool = False) -> "StoragePath":
        """ファイルを移動する

        Args:
            destination(str | StoragePath): 移動先のパス
            overwrite(bool): 上書きするかどうか。デフォルトは False。

        Returns:
            StoragePath: 移動先のパス
        """
        ...

    def delete(self) -> None:
        """ファイルを削除する"""
        ...
