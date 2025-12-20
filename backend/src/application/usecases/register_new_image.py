"""新規画像登録サービス"""

from dataclasses import dataclass
from logging import getLogger
from typing import Final

import common.concurrency.parallel as parallel

from application.service.image_deduplication import ImageDeduplicationService
from application.service.image_metadata_extractor import ImageMetadataExtractor
from application.service.tagging_result_classifier import TaggingResultClassifier
from application.storage.ports import Storage
from domain.entities.images import ImageEntry
from domain.entities.model_tag import ModelTagEntries
from domain.repositories.unit_of_work import UnitOfWorkProtocol
from domain.tagger.result import TaggerResult
from domain.tagger.tagger import Tagger
from domain.value_objects.image_hash import ImageHash


logger = getLogger(__name__)


@dataclass(frozen=True)
class _ImageEntryBinaryPair:
    """画像エントリーと画像バイナリのペア"""

    entry: ImageEntry
    binary: bytes


@dataclass(frozen=True)
class _ImageEntryBinaryPairs:
    """画像エントリーと画像バイナリのペアのリスト"""

    pairs: list[_ImageEntryBinaryPair]

    @property
    def entries(self) -> list[ImageEntry]:
        return [pair.entry for pair in self.pairs]

    @property
    def binaries(self) -> list[bytes]:
        return [pair.binary for pair in self.pairs]

    def filter_by_entry_hashes(self, allowed_hashes: set[ImageHash]) -> "_ImageEntryBinaryPairs":
        return _ImageEntryBinaryPairs([pair for pair in self.pairs if pair.entry.hash in allowed_hashes])

    def exclude_none_entries(self) -> "_ImageEntryBinaryPairs":
        return _ImageEntryBinaryPairs([pair for pair in self.pairs if pair.entry is not None])

    def __iter__(self):
        return iter(self.pairs)


class RegisterNewImageUsecase:
    """新規画像登録ユースケース"""

    REQUIRED_REPOSITORIES: Final[list[str]] = ["images", "model_tag"]

    def __init__(
        self,
        unit_of_work: UnitOfWorkProtocol,
        tagger: Tagger,
        storage: Storage,
    ) -> None:
        """RegisterNewImageUsecaseを初期化する

        Args:
            unit_of_work(UnitOfWorkProtocol): Unit of Work.次のリポジトリを管理する:
                - images(ImagesRepository): 画像リポジトリ
                - model_tag(ModelTagRepository): モデルタグリポジトリ
            tagger(Tagger): タグ付けモデル
            storage(Storage): ストレージ
        """
        self.unit_of_work = unit_of_work.subset(self.REQUIRED_REPOSITORIES)
        self.tagger = tagger
        self.storage = storage

    def _extract_metadata(self, image_file: str) -> _ImageEntryBinaryPair:
        image_binary = self.storage.read_binary(image_file)
        image_entry = ImageMetadataExtractor(storage=self.storage).extract_from_file(image_file, image_binary)
        return _ImageEntryBinaryPair(entry=image_entry, binary=image_binary)

    def _tag(self, image_binary: bytes) -> TaggerResult:
        return self.tagger.tag(image_binary)

    def handle(self, image_files: list[str], n_workers: int = 8) -> None:
        """画像ディレクトリ内のすべての画像を登録する

        Args:
            image_files(list[str]): 画像ファイルのパスのリスト
            n_workers(int): タグ付けの並列処理の最大並列数

        Raises:
            TaggingError: タグ付けに失敗した場合
        """
        if not image_files:
            logger.warning("no input files")
            return
        logger.info("total input image files: %d", len(image_files))

        # 1. バイナリデータを読み込み、メタデータを抽出する
        pairs = parallel.execute(
            func=self._extract_metadata,
            args_list=[(image_file,) for image_file in image_files],
            n_workers=n_workers,
            strategy=parallel.ExecutionStrategy.THREAD,
            show_progress=True,
            description="Extracting metadata",
            raise_on_error=False,
        )
        pairs = _ImageEntryBinaryPairs([pair for pair in pairs if not isinstance(pair, Exception)])
        pairs = pairs.exclude_none_entries()

        # 2. メタデータ抽出できなかったファイルを除外
        if not pairs.entries:
            logger.warning("no valid image entries")
            return

        # 3. 既存画像の重複チェック
        non_duplicate_image_entries = ImageDeduplicationService.filter_duplicates(
            image_entries=pairs.entries,
            images_repo=self.unit_of_work["images"],
        )
        if not non_duplicate_image_entries:
            logger.info("no image entries after duplicate check")
            return

        # 4. 重複を除外した画像のペアデータを取得
        pairs = pairs.filter_by_entry_hashes({entry.hash for entry in non_duplicate_image_entries})

        # 5. タグ付け処理
        tagger_results_raw = parallel.execute(
            func=self._tag,
            args_list=[(pair.binary,) for pair in pairs],
            n_workers=n_workers,
            strategy=parallel.ExecutionStrategy.THREAD,
            show_progress=True,
            description="Tagging images",
            raise_on_error=False,
        )

        # 6. タグ付けできた画像のみを抽出（ExceptionをNoneに変換）
        tagger_results = [result if not isinstance(result, Exception) else None for result in tagger_results_raw]
        outcome = TaggingResultClassifier.classify(pairs.entries, tagger_results)
        if not outcome.has_any_success:
            logger.warning("no valid tagged images after filtering")
            return
        logger.info("tagging result: %s", outcome.counts)

        # 7. データベースへの永続化
        with self.unit_of_work:
            # images table insert
            image_ids = self.unit_of_work["images"].insert([result.image_entry for result in outcome.success])

            # model_tag table insert
            model_tag_entries_list = [
                ModelTagEntries.from_tagger_result(image_id=image_id, tags=result.tagger_result)
                for image_id, result in zip(image_ids, outcome.success, strict=True)
            ]
            self.unit_of_work["model_tag"].insert(model_tag_entries_list)

            logger.info("total registered images: %d", len(image_ids))
            logger.info("total registered model_tag_entries: %d", len(model_tag_entries_list))
