"""画像ファイルの読み込み処理（インフラ層）

責務: ファイルI/OとPIL依存の処理のみ
"""

from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from common.exceptions import UnsupportedFileTypeError
from domain.entities.images import ImageSize


class PILImageLoader:
    """PILを使用した画像ローダー"""

    def load_binary(self, image_file: Path) -> bytes:
        """画像ファイルをバイナリデータとして読み込む

        Args:
            image_file(Path): 画像ファイルのパス

        Returns:
            bytes: 画像のバイナリデータ

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        with image_file.open("rb") as fp:
            return fp.read()

    def extract_size(self, image_binary: bytes) -> ImageSize:
        """画像のバイナリデータからサイズを抽出（PIL依存）

        Args:
            image_binary(bytes): 画像のバイナリデータ

        Returns:
            ImageSize: 画像のサイズ情報

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
        """
        try:
            image = Image.open(BytesIO(image_binary))
            return ImageSize(width=image.width, height=image.height)
        except UnidentifiedImageError as e:
            msg = f"Not supported image format: {e}"
            raise UnsupportedFileTypeError(msg) from e
        except Exception as e:
            msg = f"Failed to extract image size: {e}"
            raise UnsupportedFileTypeError(msg) from e
