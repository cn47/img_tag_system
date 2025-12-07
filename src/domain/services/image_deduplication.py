from domain.entities.images import ImageEntry
from domain.value_objects.image_hash import ImageHash


class ImageDeduplicationService:
    """画像の重複チェック・除外するサービス"""

    @staticmethod
    def filter_duplicates(
        image_entries: list[ImageEntry],
        existing_hash_set: set[ImageHash],
    ) -> list[ImageEntry]:
        """既存のハッシュセットと比較して重複を除外する

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト
            existing_hash_set(set[ImageHash]): 既存の画像ハッシュのセット

        Returns:
            list[ImageEntry]: 重複を除外した画像エントリーのリスト
        """
        return [entry for entry in image_entries if entry.hash not in existing_hash_set]
