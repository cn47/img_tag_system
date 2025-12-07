"""画像ローダーのプロトコル定義

このプロトコルは技術的な抽象化のため、common層に配置されています。
ドメイン層は技術的詳細から独立しているため、このプロトコルは使用しません。
"""

from pathlib import Path
from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

from domain.value_objects.image_size import ImageSize


class ImageLoader(Protocol):
    """画像ローダーのプロトコル

    このプロトコルはアプリケーション層とインフラ層で使用されます。
    ドメイン層は技術的詳細から独立しているため、このプロトコルを直接使用しません。
    """

    def load_binary(self, image_file: str | Path) -> bytes:
        """画像ファイルをバイナリデータとして読み込む

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            bytes: 画像のバイナリデータ
        """
        ...

    def load_image(self, image_file: str | Path) -> "PILImage":
        """画像ファイルをPILのImageオブジェクトとして読み込む

        注意: このメソッドは実装依存の型を返すため、
        インフラ層でのみ使用することを推奨します。

        Args:
            image_file(str | Path): 画像ファイルのパス

        Returns:
            PILImage: PILのImageオブジェクト（実装依存）
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
