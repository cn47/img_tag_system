from dataclasses import asdict, dataclass

from application.inference.tag_types import TaggerResult


@dataclass(frozen=True)
class ModelTagEntry:
    """タグ1つ"""

    image_id: int
    category: str
    tag: str
    score: float
    archived: bool = False


@dataclass(frozen=True)
class ModelTagEntries:
    """1画像に対する複数タグを持つ"""

    entries: list[ModelTagEntry]

    @classmethod
    def from_tagger_result(cls, image_id: int, tags: TaggerResult) -> "ModelTagEntries":
        """TaggerResultからModelTagEntriesを作成"""
        return cls(
            entries=[
                ModelTagEntry(
                    image_id,
                    str(r["category"]),
                    str(r["tag"]),
                    float(r["score"]),
                    archived=False,
                )
                for r in tags.to_dict_list()
            ],
        )

    def show(self) -> None:
        for entry in self.entries:
            print(entry)

    def to_dict_list(self) -> list[dict[str, object]]:
        """ModelTagEntriesの辞書リスト形式"""
        return [asdict(entry) for entry in self.entries]
