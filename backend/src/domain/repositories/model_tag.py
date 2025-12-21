from typing import Protocol

from domain.entities.model_tag import ModelTagEntries


class ModelTagRepository(Protocol):
    """モデルタグ情報のリポジトリ"""

    def add(self, entries: ModelTagEntries | list[ModelTagEntries]) -> None:
        """1件の画像または複数の画像に対する複数タグをまとめてADD

        内部でentriesをリストに変換してBULK ADDを呼び出す。

        Args:
            entries(ModelTagEntries | list[ModelTagEntries]): 1件の画像または複数の画像に対する複数タグ

        Returns:
            None

        Raises:
            ImageNotFoundError: 画像IDが存在しない場合
            InfrastructureError: インフラストラクチャエラー
        """
        ...

    def get(self, image_id: int) -> ModelTagEntries:
        """画像IDで1件の画像に対する複数タグを取得

        Args:
            image_id(int): 画像ID

        Returns:
            ModelTagEntries: 1件の画像に対する複数タグ
        """
        ...

    def remove_all_by_image_id(self, image_id: int) -> int:
        """画像IDで1件の画像に対するすべてのタグを削除

        Args:
            image_id(int): 画像ID

        Returns:
            int: 削除した件数
        """
        ...
