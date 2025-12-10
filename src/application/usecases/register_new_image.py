"""新規画像登録サービス"""

from logging import getLogger
from pathlib import Path
from typing import Final

from application.image_loader import ImageLoader
from application.service.image_metadata_extractor import ImageMetadataExtractor
from domain.entities.model_tag import ModelTagEntries
from domain.repositories.unit_of_work import UnitOfWorkProtocol
from domain.services.image_deduplication import ImageDeduplicationService
from domain.services.tagging_result_filter import TaggingResultFilterService
from domain.tagger.tagger import Tagger
from infrastructure.services.parallel_executor import ExecutionStrategy, execute_parallel


logger = getLogger(__name__)


class RegisterNewImageUsecase:
    """新規画像登録ユースケース"""

    REQUIRED_REPOSITORIES: Final[list[str]] = ["images", "model_tag"]

    def __init__(
        self,
        unit_of_work: UnitOfWorkProtocol,
        tagger: Tagger,
        image_loader: ImageLoader,
    ) -> None:
        """RegisterNewImageUsecaseを初期化する

        Args:
            unit_of_work(UnitOfWorkProtocol): Unit of Work.次のリポジトリを管理する:
                - images(ImagesRepository): 画像リポジトリ
                - model_tag(ModelTagRepository): モデルタグリポジトリ
            tagger(Tagger): タグ付けモデル
            image_loader(ImageLoader): 画像ローダー
        """
        self.unit_of_work = unit_of_work.subset(self.REQUIRED_REPOSITORIES)
        self.tagger = tagger
        self.image_loader = image_loader

    def handle(self, image_files: list[Path], n_workers: int = 8) -> None:
        """画像ディレクトリ内のすべての画像を登録する

        Args:
            image_files(list[Path]): 画像ファイルのパスのリスト
            n_workers(int): タグ付けの並列処理の最大並列数

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の画像があった場合
            TaggingError: タグ付けに失敗した場合
        """
        logger.info("total input image files: %d", len(image_files))

        # 1. メタデータ抽出とImageEntry作成
        image_entries = ImageMetadataExtractor(image_loader=self.image_loader).extract_from_files(image_files)

        # 2. 既存画像の重複チェック
        existing_image_entries = self.unit_of_work["images"].find_by_hashes([entry.hash for entry in image_entries])
        existing_hash_set = {entry.hash for entry in existing_image_entries}
        image_entries = ImageDeduplicationService.filter_duplicates(image_entries, existing_hash_set)

        # 3. タグ付け処理
        tagger_results_raw = execute_parallel(
            func=self.tagger.tag_image_file,
            args_list=[(str(image_entry.file_location),) for image_entry in image_entries],
            n_workers=n_workers,
            strategy=ExecutionStrategy.THREAD,
            show_progress=True,
            description="Tagging images",
            raise_on_error=False,
        )

        # 4. タグ付けできた画像のみを抽出（ExceptionをNoneに変換）
        tagger_results = [result if not isinstance(result, Exception) else None for result in tagger_results_raw]
        filtered_results = TaggingResultFilterService.filter_tagged_images(image_entries, tagger_results)

        # 5. データベースへの永続化
        with self.unit_of_work:
            # images table insert
            image_ids = self.unit_of_work["images"].insert([result.image_entry for result in filtered_results])

            # model_tag table insert
            model_tag_entries_list = [
                ModelTagEntries.from_tagger_result(image_id=image_id, tags=result.tagger_result)
                for image_id, result in zip(image_ids, filtered_results, strict=True)
            ]
            self.unit_of_work["model_tag"].insert(model_tag_entries_list)

            logger.info("total registered images: %d", len(image_ids))
            logger.info("total registered model_tag_entries: %d", len(model_tag_entries_list))
