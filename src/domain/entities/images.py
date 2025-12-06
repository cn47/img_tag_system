"""画像エンティティと値オブジェクトの定義"""

import hashlib

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from domain.services.image_loader import ImageLoader


@dataclass(frozen=True)
class ImageSize:
    """画像サイズ"""

    width: int
    height: int


@dataclass(frozen=True)
class ImageMetadata:
    """画像ファイルのメタデータ"""

    image_file: Path
    hash: str
    width: int
    height: int
    file_type: str


@dataclass(frozen=True)
class ImageEntry:
    """imagesDBへのエントリーオブジェクト"""

    image_id: int | None
    file_location: str
    width: int
    height: int
    file_type: str
    hash: str
    added_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_metadata(cls, metadata: ImageMetadata) -> "ImageEntry":
        """ImageMetadataからImageEntryを作成"""
        return cls(
            image_id=None,  # 主キーはDB側で自動生成
            file_location=metadata.image_file.as_posix(),
            width=metadata.width,
            height=metadata.height,
            file_type=metadata.file_type,
            hash=metadata.hash,
        )

    def to_dict(self) -> dict[str, object]:
        """ImageEntryの辞書"""
        return asdict(self)


class ImageMetadataFactory:
    """画像メタデータを作成する"""

    @staticmethod
    def create(
        image_file: Path,
        image_loader: "ImageLoader",
    ) -> ImageMetadata:
        """画像ファイルからメタデータを作成する

        Args:
            image_file(Path): 画像ファイルのパス
            image_loader(ImageLoader): 画像ローダー

        Returns:
            ImageMetadata: 抽出されたメタデータ

        Raises:
            FileNotFoundError: ファイルが見つからない場合
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
        """
        image_binary = image_loader.load_binary(image_file)

        image_size = image_loader.extract_size(image_binary)

        file_hash = ImageMetadataFactory._calc_sha256(image_binary)

        file_type = ImageMetadataFactory._get_file_type(image_file)

        return ImageMetadata(
            image_file=image_file,
            hash=file_hash,
            width=image_size.width,
            height=image_size.height,
            file_type=file_type,
        )

    @staticmethod
    def _calc_sha256(image_binary: bytes) -> str:
        """バイナリデータからSHA256を計算"""
        return hashlib.sha256(image_binary).hexdigest()

    @staticmethod
    def _get_file_type(image_file: Path) -> str:
        """ファイルパスからファイルタイプを取得"""
        return image_file.suffix.lower().lstrip(".")
