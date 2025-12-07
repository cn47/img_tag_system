"""画像ローダーのドメインサービスインターフェース"""

from pathlib import Path
from typing import Protocol

from domain.entities.images import ImageSize


class ImageLoader(Protocol):
    """画像ローダーのドメインサービスインターフェース"""

    def load_binary(self, image_file: str | Path) -> bytes:
        """画像ファイルをバイナリデータとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            bytes: 画像のバイナリデータ

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        ...

    def extract_size(self, image_file: str | Path) -> ImageSize:
        """画像からサイズを抽出する

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            ImageSize: 画像のサイズ情報

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
        """
        ...
