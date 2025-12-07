from logging import getLogger
from pathlib import Path

from common.exceptions import UnsupportedFileTypeError
from domain.entities.images import ImageEntry, ImageMetadataFactory
from domain.services.image_loader import ImageLoader


logger = getLogger(__name__)


class ImageMetadataExtractorService:
    """画像メタデータ抽出サービス"""

    def __init__(self, image_loader: ImageLoader) -> None:
        self.image_loader = image_loader

    def extract_from_file(self, image_file: Path) -> ImageEntry | None:
        """画像ファイルからImageEntryを作成

        Args:
            image_file(Path): 画像ファイルのパス

        Returns:
            ImageEntry | None: 作成されたImageEntry、失敗時はNone
        """
        try:
            metadata = ImageMetadataFactory.create(image_file=image_file, image_loader=self.image_loader)
            return ImageEntry.from_metadata(metadata)
        except UnsupportedFileTypeError:
            logger.warning("skipped: Unsupported file type: %s", image_file)
            return None
        except Exception as e:
            logger.warning("skipped: Failed to load image: %s: %s", image_file, e)
            return None

    def extract_from_files(self, image_files: list[Path]) -> list[ImageEntry]:
        """複数の画像ファイルからImageEntryリストを作成

        Args:
            image_files(list[Path]): 画像ファイルのリスト

        Returns:
            list[ImageEntry]: 作成されたImageEntryリスト

        TODO:  並列処理を検討
        """
        image_entries: list[ImageEntry] = []
        for image_file in image_files:
            image_entry = self.extract_from_file(image_file)
            if image_entry is not None:
                image_entries.append(image_entry)
        return image_entries
