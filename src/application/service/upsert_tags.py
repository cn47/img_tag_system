"""既存画像のタグをアップサートするサービスモジュール"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from pathlib import Path

from tqdm import tqdm

from application.inference.tag_types import TaggerResult
from application.inference.tagger import Tagger
from application.repositories.images import ImagesRepository
from application.repositories.model_tag import ModelTagRepository
from domain.entities.images import ImageEntry
from domain.entities.model_tag import ModelTagEntries
from exceptions import ImageNotFoundError, TaggingError, UnsupportedFileTypeError


logger = getLogger(__name__)


class UpsertTagsService:
    """既存画像のタグをアップサートするサービス"""

    def __init__(self, images_repo: ImagesRepository, model_tag_repo: ModelTagRepository, tagger: Tagger) -> None:
        """UpsertTagsServiceを初期化する

        Args:
            images_repo(ImagesRepository): 画像リポジトリ
            model_tag_repo(ModelTagRepository): モデルタグリポジトリ
            tagger(Tagger): タグ付けモデル
        """
        self.images_repo = images_repo
        self.model_tag_repo = model_tag_repo
        self.tagger = tagger

        self.tagger.initialize()
        logger.info("Service initialized!")

    def upsert_one(self, image_file: str) -> None:
        """1つの画像のタグをアップサートする

        Args:
            image_file(str): 画像ファイル

        Raises:
            ImageNotFoundError: 画像が見つからない場合
            TaggingError: タグ付けに失敗した場合
            UnsupportedFileTypeError: サポートされていないファイル形式の画像があった場合
        """
        logger.info(f"Upserting tags for image_file: {image_file}...")

        # 画像エントリを取得
        image_entry = ImageEntry.from_file(image_file=Path(image_file))
        image_entry = self.images_repo.find_by_hash(image_entry.hash)
        image_id = image_entry.image_id

        if image_entry is None:
            msg = f"image not found: image_id={image_id}"
            raise ImageNotFoundError(msg)

        # タグ付けを実行
        tagger_result = self.tagger.tag_image_file(image_file=image_entry.file_location)

        # タグをアップサート(insertメソッドがINSERT OR REPLACEなので、これでアップサートになる)
        model_tag_entries = ModelTagEntries.from_tagger_result(image_id=image_id, tags=tagger_result)
        self.model_tag_repo.insert(model_tag_entries)

        logger.info(f"Upserting tags completed for image_id: {image_id}")

    def _upsert_image_tags(self, image_id: int) -> tuple[int, TaggerResult | None]:
        """1つの画像のタグをアップサートする（内部メソッド）

        Args:
            image_id(int): 画像ID

        Returns:
            tuple[int, TaggerResult | None]: (image_id, tagger_result)
                タグ付けできなかった場合はNoneを返す
        """
        try:
            # 画像エントリを取得
            image_entry = self.images_repo.get(image_id)
            if image_entry is None:
                logger.warning(f"skipped: image not found: image_id={image_id}")
                return (image_id, None)

            # タグ付けを実行
            tagger_result = self.tagger.tag_image_file(image_file=image_entry.file_location)
            return (image_id, tagger_result)
        except UnsupportedFileTypeError as e:
            logger.warning(f"skipped: Unsupported file type: image_id={image_id}: {e}")
            return (image_id, None)
        except TaggingError as e:
            logger.warning(f"skipped: Tagging failed for image_id={image_id}: {e}")
            return (image_id, None)

    def _find_existing_image_ids(self, image_entries: list[ImageEntry]) -> list[int]:
        """画像エントリーリストから既存の画像IDを取得する

        hash衝突をチェックして、既存の画像IDを返す

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト

        Returns:
            list[int]: 既存の画像IDのリスト
        """
        existing_image_entries = self.images_repo.find_by_hashes([entry.hash for entry in image_entries])
        return [entry.image_id for entry in existing_image_entries if entry.image_id is not None]

    def upsert_many(self, image_files: list[str], n_workers: int = 8) -> None:
        """画像ディレクトリ内のすべての画像のタグを並列でアップサートする

        Args:
            image_files(list[str]): 画像ファイルのリスト
            n_workers(int): タグ付けの並列処理の最大並列数

        Raises:
            ImageNotFoundError: 画像が見つからない場合（一部でも）
            TaggingError: タグ付けに失敗した場合（一部でも）
            UnsupportedFileTypeError: サポートされていないファイル形式の画像があった場合（一部でも）
        """
        logger.info(f"total input image files: {len(image_files)}")

        # 画像エントリを作成
        image_entries = [ImageEntry.from_file(image_file=Path(image_file)) for image_file in image_files]

        # 既存の画像IDを取得
        image_ids = self._find_existing_image_ids(image_entries)
        if not image_ids:
            logger.warning("No existing images found in the input image_files")
            return

        logger.info(f"total existing image_ids: {len(image_ids)}")

        # 並列でタグ付けを実行
        tagger_results: dict[int, TaggerResult | None] = {}
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(self._upsert_image_tags, image_id): image_id for image_id in image_ids}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Tagging images"):
                image_id = futures[future]
                _, tagger_result = future.result()
                tagger_results[image_id] = tagger_result

        # タグ付けできた画像のみを処理
        successful_results = {
            image_id: tagger_result for image_id, tagger_result in tagger_results.items() if tagger_result is not None
        }

        if not successful_results:
            logger.warning("No images were successfully tagged")
            return

        # タグをアップサート
        model_tag_entries_list = [
            ModelTagEntries.from_tagger_result(image_id=image_id, tags=tagger_result)
            for image_id, tagger_result in successful_results.items()
        ]
        self.model_tag_repo.insert(model_tag_entries_list)

        logger.info(f"total upserted images: {len(successful_results)}")
        logger.info(f"total upserted model_tag_entries: {len(model_tag_entries_list)}")
