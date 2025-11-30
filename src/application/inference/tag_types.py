"""Taggerのタグカテゴリとタグスコアを表現する型定義モジュール"""

from dataclasses import InitVar, dataclass, field


@dataclass(frozen=True)
class TagScore:
    tag: str
    score: float


class TagScoreSequence(tuple):
    """タグスコアのタプルにトップ要素アクセスを追加する。

    Example:
        tags.character # -> TagScoreSequence((TagScore(tag='hatsune_(princess_connect!)', score=5.606165885925293), TagScore(tag='hatsune_(summer)_(princess_connect!)', score=3.5743813514709473)))
        tags.character.tag # -> 'hatsune_(princess_connect!)'
        tags.character.score # -> 5.606165885925293
    """

    @property
    def tag(self) -> str | None:
        # 先頭要素が存在する場合、その tag を返す。存在しなければ None を返す。
        if len(self) > 0:
            return self[0].tag
        return None

    @property
    def score(self) -> float | None:
        # 先頭要素が存在する場合、その score を返す。存在しなければ None を返す。
        if len(self) > 0:
            return self[0].score
        return None


@dataclass
class TaggerResult:
    tags: InitVar[dict[str, list[tuple[str, float]]]]

    rating: TagScoreSequence = field(default_factory=TagScoreSequence)
    copyright: TagScoreSequence = field(default_factory=TagScoreSequence)
    character: TagScoreSequence = field(default_factory=TagScoreSequence)
    artist: TagScoreSequence = field(default_factory=TagScoreSequence)
    general: TagScoreSequence = field(default_factory=TagScoreSequence)

    # dbでは参照しないのでメタデータは外す
    # meta: TagScoreSequence = field(default_factory=TagScoreSequence)
    # year: TagScoreSequence = field(default_factory=TagScoreSequence)

    _original_tags: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    def __post_init__(self, tags: dict):
        self._original_tags = tags
        for category, pairs in self._original_tags.items():
            tag_scores = TagScoreSequence(TagScore(tag, score) for tag, score in pairs)
            setattr(self, category, tag_scores)

    @property
    def categories(self) -> list[str]:
        return list(self._original_tags.keys())

    def show(self) -> None:
        """タグ情報をコンソールに表示する"""
        for category in ["rating", "copyright", "character", "artist", "general"]:
            items = self._original_tags.get(category, [])
            if not items:
                continue

            print(f"\n=== {category.upper()} ===")
            for tag, score in items:
                print(f"{tag}: {score:.3f}")

    def to_dict_list(self) -> list[dict[str, str | float]]:
        """タグ情報を辞書のリスト形式で取得する

        Returns:
            list[dict[str, str | float]]: タグ情報のリスト。各辞書は 'category', 'tag', 'score' キーを持つ。

        例:
            [
                {'category': 'general', 'tag': 'tag1', 'score': 0.95},
                {'category': 'artist', 'tag': 'tag2', 'score': 0.85},
                ...
            ]
        """
        result = []
        for category, items in self._original_tags.items():
            for tag, score in items:
                result.append({"category": category, "tag": tag, "score": score})
        return result
