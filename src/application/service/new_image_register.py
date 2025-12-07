"""新規画像登録サービス"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from pathlib import Path

from tqdm import tqdm
from typing_extensions import deprecated

from common.exceptions import DuplicateImageError, ImageNotFoundError, TaggingError, UnsupportedFileTypeError
from domain.entities.images import ImageEntry, ImageMetadataFactory
from domain.entities.model_tag import ModelTagEntries
from domain.repositories.images import ImagesRepository
from domain.repositories.model_tag import ModelTagRepository
from domain.services.image_deduplication import ImageDeduplicationService
from domain.services.image_metadata_extractor import ImageMetadataExtractorService
from domain.services.tagging_result_filter import TaggingResultFilterService
from domain.tagger.result import TaggerResult
from domain.tagger.tagger import Tagger
from infrastructure.services.image_loader import PILImageLoader


logger = getLogger(__name__)


class NewImageRegisterService:
    """新規画像登録サービス"""

    def __init__(self, images_repo: ImagesRepository, model_tag_repo: ModelTagRepository, tagger: Tagger) -> None:
        """NewImageRegisterServiceを初期化する

        Args:
            images_repo(ImagesRepository): 画像リポジトリ
            model_tag_repo(ModelTagRepository): モデルタグリポジトリ
            tagger(Tagger): タグ付けモデル
        """
        self.images_repo = images_repo
        self.model_tag_repo = model_tag_repo
        self.tagger = tagger
        self.image_loader = PILImageLoader()  # TODO: インフラ層の実装を注入に切り替える

    @deprecated("Use register instead")
    def register_one(self, image_file: str | Path) -> None:
        """1枚の画像を登録する

        Args:
            image_file(str | Path): 画像ファイル

        Raises:
            DuplicateImageError: すでに登録済みの画像が存在する場合
            ImageNotFoundError: 画像が見つからない場合
            TaggingError: タグ付けに失敗した場合
            UnsupportedFileTypeError: サポートされていないファイル形式の画像があった場合
        """
        logger.info("Registering image: %s...", image_file)

        image_path = Path(image_file)
        image_entry = self._create_image_entry_from_file(image_path)

        if image_entry is None:
            raise UnsupportedFileTypeError(f"Failed to create image entry: {image_file}")

        # images table insert
        try:
            image_id = self.images_repo.insert(image_entry)[0]
        except DuplicateImageError:
            image_entry = self.images_repo.find_by_hash(image_entry.hash)
            if image_entry is None:
                msg = f"image not found in images table: {image_file}"
                raise ImageNotFoundError(msg) from None

            image_id = image_entry.image_id
            logger.info("skipped registering image because it already exists in images table")
            return

        logger.info("upserting tags for image")

        # tagging
        tagger_result = self.tagger.tag_image_file(image_file=image_file)

        # model_tag table insert
        model_tag_entries = ModelTagEntries.from_tagger_result(image_id=image_id, tags=tagger_result)
        self.model_tag_repo.insert(model_tag_entries)

        logger.info("Registering one image completed: %s", image_file)

    def _tag_image_entries(self, image_entries: list[ImageEntry], n_workers: int) -> list[TaggerResult | None]:
        """画像のエントリーリストをタグ付けする

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト
            n_workers(int): タグ付けの並列処理の最大並列数

        Returns:
            list[TaggerResult | None]: タグ付け結果のリスト。タグ付けできなかった画像はNoneを返す。
        """
        tagger_results: list[TaggerResult | None] = [None] * len(image_entries)
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {
                executor.submit(self.tagger.tag_image_file, image_file=Path(str(image_entry.file_location))): i
                for i, image_entry in enumerate(image_entries)
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc="Tagging images"):
                i = futures[future]
                try:
                    tagger_results[i] = future.result()
                except UnsupportedFileTypeError as e:
                    logger.warning("skipped: Unsupported file type: %s: %s", str(image_entries[i].file_location), e)
                except TaggingError as e:
                    logger.warning("skipped: Tagging failed for %s: %s", str(image_entries[i].file_location), e)

        return tagger_results

    def handle(self, image_files: list[str | Path], n_workers: int = 8) -> None:
        """画像ディレクトリ内のすべての画像を登録する

        Args:
            image_files(list[str | Path]): 画像ファイルのリスト
            n_workers(int): タグ付けの並列処理の最大並列数

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の画像があった場合
            TaggingError: タグ付けに失敗した場合
        """
        logger.info("total input image files: %d", len(image_files))

        # 1. メタデータ抽出とImageEntry作成
        image_files = [Path(image_file) if isinstance(image_file, str) else image_file for image_file in image_files]
        image_entries = ImageMetadataExtractorService(image_loader=self.image_loader).extract_from_files(image_files)

        # 2. 既存画像の重複チェック
        existing_image_entries = self.images_repo.find_by_hashes([entry.hash for entry in image_entries])
        existing_hash_set = {entry.hash for entry in existing_image_entries}
        image_entries = ImageDeduplicationService.filter_duplicates(image_entries, existing_hash_set)

        # 3. タグ付け処理
        tagger_results = self._tag_image_entries(image_entries, n_workers=n_workers)

        # 4. タグ付けできた画像のみを抽出
        filtered_results = TaggingResultFilterService.filter_tagged_images(image_entries, tagger_results)

        # 5. データベースへの永続化

        # images table insert
        image_ids = self.images_repo.insert([result.image_entry for result in filtered_results])

        # model_tag table insert
        model_tag_entries_list = [
            ModelTagEntries.from_tagger_result(image_id=image_id, tags=result.tagger_result)
            for image_id, result in zip(image_ids, filtered_results, strict=True)
        ]
        self.model_tag_repo.insert(model_tag_entries_list)

        logger.info("total registered images: %d", len(image_ids))
        logger.info("total registered model_tag_entries: %d", len(model_tag_entries_list))
