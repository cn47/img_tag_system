from io import BytesIO
from logging import getLogger

from PIL import Image, UnidentifiedImageError

from application.storage.ports import Storage
from domain.entities.images import ImageEntry, ImageMetadataFactory
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_size import ImageSize


logger = getLogger(__name__)


class ImageMetadataExtractor:
    """画像メタデータ抽出

    ファイルI/O、画像読み込みを処理し、
    ImageMetadataFactoryを呼び出してメタデータを作成します。
    """

    def __init__(self, storage: Storage) -> None:
        """ImageMetadataExtractorを初期化する

        Args:
            image_loader(ImageLoader): 画像ローダー
        """
        self._storage = storage

    def extract_from_file(self, image_file: str, image_binary: bytes | None = None) -> ImageEntry | None:
        """画像ファイルからImageEntryを作成

        Args:
            image_file(str): 画像ファイルのパス
            image_binary(bytes | None): 画像バイナリデータ
                デフォルトはNone。Noneの場合storageからimage_fileを読み込む。
        Returns:
            ImageEntry | None: 作成されたImageEntry、失敗時はNone
        """
        try:
            image_binary = image_binary or self._storage.read_binary(image_file)
            image = Image.open(BytesIO(image_binary))
            file_size = self._storage.get_size(image_file)
            file_type = self._storage.get_file_extension(image_file)

            file_location = FileLocation(image_file)
            image_size = ImageSize(width=image.width, height=image.height)

            metadata = ImageMetadataFactory.create(
                file_location=file_location,
                image_binary=image_binary,
                image_size=image_size,
                file_type=file_type,
                file_size=file_size,
            )
            return ImageEntry.from_metadata(metadata)
        except UnidentifiedImageError:
            logger.warning("skipped: Unsupported file type: %s", image_file)
            return None
        except Exception as e:
            logger.warning("skipped: Failed to load image: %s: %s", image_file, e)
            return None
