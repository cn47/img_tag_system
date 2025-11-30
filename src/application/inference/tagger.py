from pathlib import Path
from typing import Protocol

from application.inference.tag_types import TaggerResult


class Tagger(Protocol):
    """タグ付けモデル"""

    def initialize(self) -> None:
        pass

    def tag_image_file(self, image_file: str | Path) -> TaggerResult:
        """画像ファイルに対してタグ推論 + カテゴリ分類まで行う

        Args:
            image_file(str | Path): 画像ファイル

        Returns:
            TaggerResult: タグ推論結果

        Raises:
            UnsupportedFileTypeError: サポートされていないファイル形式の場合
            RuntimeError: モデルセッションが初期化されていない場合
            TaggingError: タグ推論に失敗した場合
        """
        pass
