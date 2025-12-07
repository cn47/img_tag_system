import hashlib

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from domain.value_objects.image_size import ImageSize


if TYPE_CHECKING:
    from domain.services.image_loader import ImageLoader


@dataclass(frozen=True)
class ImageMetadata:
    """画像ファイルのメタデータ"""

    image_file: Path
    hash: ImageHash
    size: ImageSize
    file_type: str


@dataclass(frozen=True)
class ImageEntry:
    """imagesDBへのエントリーオブジェクト"""

    image_id: int | None
    file_location: FileLocation
    width: int
    height: int
    file_type: str
    hash: ImageHash
    added_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_metadata(cls, metadata: ImageMetadata) -> "ImageEntry":
        """ImageMetadataからImageEntryを作成"""
        return cls(
            image_id=None,  # 主キーはDB側で自動生成
            file_location=FileLocation(metadata.image_file.as_posix()),
            width=metadata.size.width,
            height=metadata.size.height,
            file_type=metadata.file_type,
            hash=metadata.hash,
        )

    def to_dict(self) -> dict[str, object]:
        """ImageEntryの辞書"""
        result = asdict(self)
        result["hash"] = str(self.hash)
        result["file_location"] = str(self.file_location)
        return result


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

        image_size = image_loader.extract_size(image_file)

        file_hash = ImageMetadataFactory._calc_sha256(image_binary)

        file_type = ImageMetadataFactory._get_file_type(image_file)

        return ImageMetadata(
            image_file=image_file,
            hash=file_hash,
            size=image_size,
            file_type=file_type,
        )

    @staticmethod
    def _calc_sha256(image_binary: bytes) -> ImageHash:
        """バイナリデータからSHA256を計算してImageHash値オブジェクトを返す"""
        hash_str = hashlib.sha256(image_binary).hexdigest()
        return ImageHash(hash_str)

    @staticmethod
    def _get_file_type(image_file: Path) -> str:
        """ファイルパスからファイルタイプを取得"""
        return image_file.suffix.lower().lstrip(".")
