from dataclasses import dataclass

from domain.entities.images import ImageEntry
from domain.tagger.result import TaggerResult


@dataclass(frozen=True)
class TaggedImageEntry:
    """タグ付け済みの画像エントリー"""

    image_entry: ImageEntry
    tagger_result: TaggerResult


@dataclass(frozen=True)
class TaggingOutcome:
    """タグ付けの結果"""

    success: list[TaggedImageEntry]
    failure: list[ImageEntry]
    empty: list[ImageEntry]

    @property
    def has_any_success(self) -> bool:
        """タグ付けが1つでも成功したかどうかを返す"""
        return len(self.success) > 0

    @property
    def counts(self) -> dict[str, int]:
        """タグ付けの結果の数を返す"""
        return {
            "success": len(self.success),
            "failure": len(self.failure),
            "empty": len(self.empty),
        }

    @property
    def total_count(self) -> int:
        """タグ付けの結果の合計数を返す"""
        return len(self.success) + len(self.failure) + len(self.empty)


class TaggingResultClassifier:
    """タグ付け結果を分類するクラス"""

    @staticmethod
    def classify(
        image_entries: list[ImageEntry],
        tagger_results: list[TaggerResult | None],
    ) -> TaggingOutcome:
        """タグ付け結果を分類する

        Args:
            image_entries(list[ImageEntry]): 画像エントリーのリスト
            tagger_results(list[TaggerResult | None]): タグ付け結果のリスト。Noneはタグ付けできなかった画像を示す。

        Returns:
            TaggingOutcome: タグ付けの結果
        """
        success, failure, empty = [], [], []
        for entry, result in zip(image_entries, tagger_results, strict=True):
            if result is None:
                failure.append(entry)
            elif result.is_empty():
                empty.append(entry)
            else:
                success.append(TaggedImageEntry(image_entry=entry, tagger_result=result))

        return TaggingOutcome(success=success, failure=failure, empty=empty)
