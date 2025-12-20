from typing import Protocol

from domain.tagger.result import TaggerResult


class Tagger(Protocol):
    """タグ付けモデル"""

    def initialize(self) -> None: ...

    def tag(self, image_binary: bytes) -> TaggerResult:
        """画像バイナリに対してタグ推論 + カテゴリ分類まで行う

        Args:
            image_binary(bytes): 画像バイナリ

        Returns:
            TaggerResult: タグ推論結果

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
            RuntimeError: モデルセッションが初期化されていない場合
            TaggingError: タグ推論に失敗した場合
        """
        ...
