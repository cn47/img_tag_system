from pathlib import Path
from typing import Protocol

from PIL.Image import Image as PILImage

from domain.value_objects.image_size import ImageSize


# TODO: ローカル依存、PIL依存なので


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

    def load_image(self, image_file: str | Path) -> PILImage:
        """画像ファイルをPILのImageオブジェクトとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス
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
