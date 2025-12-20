from domain.entities.images import ImageEntry
from domain.repositories.images import ImagesRepository


class ImageDeduplicationService:
    """画像の重複チェック・除外するサービス"""

    @staticmethod
    def filter_duplicates(
        image_entries: list[ImageEntry],
        images_repo: ImagesRepository,
    ) -> list[ImageEntry]:
        """既存の画像ハッシュのセットと比較して重複を除外する

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト
            images_repo(ImagesRepository): 画像リポジトリ

        Returns:
            list[ImageEntry]: 重複を除外した画像エントリーのリスト
        """
        existing_image_entries = images_repo.find_by_hashes([entry.hash for entry in image_entries])
        existing_hash_set = {entry.hash for entry in existing_image_entries}
        return [entry for entry in image_entries if entry.hash not in existing_hash_set]
