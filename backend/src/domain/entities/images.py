from dataclasses import asdict, dataclass
from datetime import datetime

from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from domain.value_objects.image_size import ImageSize


@dataclass(frozen=True)
class ImageMetadata:
    """画像ファイルのメタデータ"""

    file_location: FileLocation
    hash: ImageHash
    size: ImageSize
    file_type: str
    file_size: int


@dataclass(frozen=True)
class ImageEntry:
    """imagesDBへのエントリーオブジェクト"""

    image_id: int | None
    file_location: FileLocation
    width: int
    height: int
    file_type: str
    hash: ImageHash
    file_size: int
    added_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_metadata(cls, metadata: ImageMetadata) -> "ImageEntry":
        """ImageMetadataからImageEntryを作成"""
        return cls(
            image_id=None,  # 主キーはDB側で自動生成
            file_location=metadata.file_location,
            width=metadata.size.width,
            height=metadata.size.height,
            file_type=metadata.file_type,
            hash=metadata.hash,
            file_size=metadata.file_size,
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
        file_location: FileLocation,
        image_binary: bytes,
        image_size: ImageSize,
        file_type: str,
        file_size: int,
    ) -> ImageMetadata:
        """既に読み込まれたデータからメタデータを作成する

        Args:
            file_location(FileLocation): ファイルの場所
            image_binary(bytes): 画像のバイナリデータ
            image_size(ImageSize): 画像のサイズ（幅と高さ）
            file_type(str): ファイルタイプ
            file_size(int): ファイルサイズ（バイト数）

        Returns:
            ImageMetadata: 抽出されたメタデータ
        """
        file_hash = ImageHash.from_binary(image_binary)

        return ImageMetadata(
            file_location=file_location,
            hash=file_hash,
            size=image_size,
            file_type=file_type,
            file_size=file_size,
        )
