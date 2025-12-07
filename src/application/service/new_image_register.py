"""新規画像登録サービス"""

from logging import getLogger
from pathlib import Path

from domain.entities.model_tag import ModelTagEntries
from domain.repositories.images import ImagesRepository
from domain.repositories.model_tag import ModelTagRepository
from domain.services.image_deduplication import ImageDeduplicationService
from domain.services.image_metadata_extractor import ImageMetadataExtractorService
from domain.services.tagging_result_filter import TaggingResultFilterService
from domain.tagger.tagger import Tagger
from infrastructure.services.image_loader import PILImageLoader
from infrastructure.services.parallel_executor import ExecutionStrategy, execute_parallel


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
        tagger_results = execute_parallel(
            func=self.tagger.tag_image_file,
            args_list=[image_entry.file_location for image_entry in image_entries],
            n_workers=n_workers,
            strategy=ExecutionStrategy.THREAD,
            show_progress=True,
            description="Tagging images",
            raise_on_error=False,
        )

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
