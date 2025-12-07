from logging import getLogger
from pathlib import Path

from common.exceptions import UnsupportedFileTypeError
from common.image_loader import ImageLoader
from domain.entities.images import ImageEntry, ImageMetadataFactory
from domain.value_objects.file_location import FileLocation


logger = getLogger(__name__)


class ImageMetadataExtractor:
    """画像メタデータ抽出

    ファイルI/O、画像読み込みを処理し、
    ImageMetadataFactoryを呼び出してメタデータを作成します。
    """

    def __init__(self, image_loader: ImageLoader) -> None:
        """ImageMetadataExtractorを初期化する

        Args:
            image_loader(ImageLoader): 画像ローダー
        """
        self.image_loader = image_loader

    def extract_from_file(self, image_file: Path) -> ImageEntry | None:
        """画像ファイルからImageEntryを作成

        Args:
            image_file(Path): 画像ファイルのパス

        Returns:
            ImageEntry | None: 作成されたImageEntry、失敗時はNone
        """
        try:
            image_binary = self.image_loader.load_binary(image_file)
            image_size = self.image_loader.extract_size(image_file)
            file_size = self.image_loader.get_file_size(image_file)
            file_type = self._get_file_type(image_file)

            file_location = FileLocation(image_file.as_posix())
            metadata = ImageMetadataFactory.create(
                file_location=file_location,
                image_binary=image_binary,
                image_size=image_size,
                file_type=file_type,
                file_size=file_size,
            )
            return ImageEntry.from_metadata(metadata)
        except UnsupportedFileTypeError:
            logger.warning("skipped: Unsupported file type: %s", image_file)
            return None
        except Exception as e:
            logger.warning("skipped: Failed to load image: %s: %s", image_file, e)
            return None

    @staticmethod
    def _get_file_type(image_file: Path) -> str:
        """ファイルパスからファイルタイプを取得"""
        return image_file.suffix.lower().lstrip(".")

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
