from typing import Protocol

from domain.entities.model_tag import ModelTagEntries


class ModelTagRepository(Protocol):
    """モデルタグ情報のリポジトリ"""

    def insert(self, entries: ModelTagEntries | list[ModelTagEntries]) -> None:
        """1件の画像または複数の画像に対する複数タグをまとめてINSERT

        内部でentriesをリストに変換してBULK INSERTを呼び出す。

        Args:
            entries(ModelTagEntries | list[ModelTagEntries]): 1件の画像または複数の画像に対する複数タグ

        Returns:
            None

        Raises:
            ImageNotFoundError: 画像IDが存在しない場合
            InfrastructureError: インフラストラクチャエラー
        """
        ...

    def list_by_image_id(self, image_id: int) -> ModelTagEntries:
        """画像IDで複数タグを取得

        Args:
            image_id(int): 画像ID

        Returns:
            ModelTagEntries: 画像に対するすべてのタグ
        """
        ...

    def find_tagged_image_ids(self, image_ids: list[int]) -> set[int]:
        """画像IDのリストでタグ付け済みの画像IDの集合を取得

        Args:
            image_ids(list[int]): 画像IDのリスト

        Returns:
            set[int]: タグ付け済みの画像IDの集合
        """
        ...

    def delete_all_by_image_id(self, image_id: int) -> int:
        """画像に対するすべてのタグを削除

        Args:
            image_id(int): 画像ID

        Returns:
            int: 削除した件数
        """
        ...

    def archive(self, image_id: int, category: str, tag: str) -> int:
        """指定したタグをアーカイブし アーカイブした件数を返す

        内部でentriesを作成してarchive_manyを呼び出す。
        実処理はarchive_manyで行う。

        Args:
            image_id(int): 画像ID
            category(str): カテゴリ
            tag(str): タグ

        Returns:
            int: アーカイブした件数

        Raises:
            ImageNotFoundError: 画像IDが存在しない場合
            InfrastructureError: インフラストラクチャエラー
        """
        ...

    def archive_many(self, entries: ModelTagEntries) -> int:
        """複数タグをまとめてアーカイブし アーカイブした件数を返す

        Args:
            entries(ModelTagEntries): 複数タグ

        Returns:
            int: アーカイブした件数
        """
        ...
