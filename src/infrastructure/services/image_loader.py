from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from domain.exceptions import UnsupportedFileTypeError
from domain.value_objects.image_size import ImageSize


class PILImageLoader:
    """PILを使用した画像ローダー"""

    @staticmethod
    def load_binary(image_file: str | Path) -> bytes:
        """画像ファイルをバイナリデータとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            bytes: 画像のバイナリデータ

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        with Path(image_file).open("rb") as fp:
            return fp.read()

    @classmethod
    def load_image(cls, image_file: str | Path) -> Image.Image:
        """画像ファイルをPILのImageオブジェクトとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            PILImage: PILのImageオブジェクト
        """
        try:
            binary = cls.load_binary(image_file)
            return Image.open(BytesIO(binary))
        except UnidentifiedImageError as e:
            raise UnsupportedFileTypeError(f"Not supported image format: {image_file}") from e

    @classmethod
    def extract_size(cls, image_file: str | Path) -> ImageSize:
        """画像のバイナリデータからサイズを抽出（PIL依存）

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            ImageSize: 画像のサイズ情報

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
        """
        image = cls.load_image(image_file)
        return ImageSize(width=image.width, height=image.height)

    @staticmethod
    def get_file_size(image_file: str | Path) -> int:
        """画像ファイルのサイズ（バイト数）を取得する

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            int: ファイルサイズ（バイト数）

        Raises:
            FileNotFoundError: ファイルが見つからない場合
        """
        return Path(image_file).stat().st_size
