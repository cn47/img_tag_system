from pathlib import Path
from typing import Protocol

from domain.value_objects.image_size import ImageSize


class ImageObject(Protocol):
    @property
    def width(self) -> int: ...

    @property
    def height(self) -> int: ...


class ImageLoader(Protocol):
    """画像ローダー"""

    def load_binary(self, image_file: str | Path) -> bytes:
        """画像ファイルをバイナリデータとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            bytes: 画像のバイナリデータ
        """
        ...

    def load_image(self, image_file: str | Path) -> ImageObject:
        """画像ファイルをPILのImageオブジェクトとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            ImageObject: 画像オブジェクト
        """
        ...

    def extract_size(self, image_file: str | Path) -> ImageSize:
        """画像からサイズを抽出する

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            ImageSize: 画像のサイズ情報
        """
        ...

    def get_file_size(self, image_file: str | Path) -> int:
        """画像ファイルのサイズ（バイト数）を取得する

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            int: ファイルサイズ（バイト数）
        """
        ...
