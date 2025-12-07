from dataclasses import dataclass

from domain.entities.images import ImageEntry
from domain.tagger.result import TaggerResult


@dataclass(frozen=True)
class TaggedImageEntry:
    """タグ付け済みの画像エントリー"""

    image_entry: ImageEntry
    tagger_result: TaggerResult


class TaggingResultFilterService:
    """タグ付け結果をフィルタリングするサービス"""

    @staticmethod
    def filter_tagged_images(
        image_entries: list[ImageEntry],
        tagger_results: list[TaggerResult | None],
    ) -> list[TaggedImageEntry]:
        """タグ付けできた画像のみを抽出する

        タグ付けできなかった画像は登録対象外とする

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト
            tagger_results(list[TaggerResult | None]): タグ付け結果のリスト。Noneはタグ付けできなかった画像を示す。

        Returns:
            list[TaggedImageEntry]: タグ付けできた画像エントリーのリスト
        """
        return [
            TaggedImageEntry(image_entry=entry, tagger_result=result)
            for entry, result in zip(image_entries, tagger_results, strict=True)
            if result is not None
        ]
