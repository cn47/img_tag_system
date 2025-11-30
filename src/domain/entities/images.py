import hashlib

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class ImageMetadata:
    """画像ファイルのメタデータ"""

    image_file: Path
    hash: str
    width: int
    height: int
    file_type: str


class ImageMetadataFactory:
    """画像ファイルのメタデータを扱うクラス"""

    @classmethod
    def from_file(cls, image_file: str | Path) -> ImageMetadata:
        """画像ファイルの情報を取得してImageInfoオブジェクトを返す"""
        image_file = Path(image_file)

        width, height = cls._get_image_size(image_file)
        file_hash = cls._calc_sha256(image_file)
        file_type = cls._get_file_type(image_file)

        return ImageMetadata(
            image_file=image_file,
            hash=file_hash,
            width=width,
            height=height,
            file_type=file_type,
        )

    @staticmethod
    def _calc_sha256(image_file: Path) -> str:
        """ファイル全体のSHA256を計算"""
        with image_file.open("rb") as fp:
            return hashlib.sha256(fp.read()).hexdigest()

    @staticmethod
    def _get_image_size(image_file: Path) -> tuple[int, int]:
        """画像ファイルの幅と高さを取得"""
        with Image.open(image_file) as image:
            return image.width, image.height

    @staticmethod
    def _get_file_type(image_file: Path) -> str:
        """画像ファイルの形式を取得"""
        return image_file.suffix.lower().lstrip(".")


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
    def from_file(cls, image_file: Path) -> "ImageEntry":
        """画像ファイルからImageEntryを作成"""
        metadata = ImageMetadataFactory.from_file(image_file)
        return cls(
            image_id=None,  # 主キーはDB側で自動生成
            file_location=metadata.image_file.as_posix(),
            width=metadata.width,
            height=metadata.height,
            file_type=metadata.file_type,
            hash=metadata.hash,
        )

    def to_dict(self) -> dict[str, object]:
        """ImageEntryの辞書形式"""
        return asdict(self)
