from typing import Protocol

from domain.entities.images import ImageEntry
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash


"""
get_xxx -> 主キーで1件取得
find_by_xxx -> 任意条件で取得(1件でも複数件でも)
list_xxx -> 複数件(コレクション)取得。全件または範囲指定
bulk_insert -> 複数件をまとめてINSERT
collectionオブジェクトのように扱えるようにする
"""


class ImagesRepository(Protocol):
    """imagesテーブルのリポジトリ"""

    def add(self, entries: ImageEntry | list[ImageEntry]) -> list[int]:
        """1件の画像または複数の画像をまとめてADDして主キーのリストを返す

        内部でentriesをリストに変換してBULK ADDを呼び出す。

        Args:
            entries(ImageEntry | list[ImageEntry]): 1件の画像または複数の画像

        Returns:
            list[int]: 主キーのリスト

        Raises:
            DuplicateImageError: 重複するハッシュが存在する場合
            InfrastructureError: インフラストラクチャエラー
        """
        ...

    def remove(self, image_ids: int | list[int]) -> None:
        """主キーで削除

        Args:
            image_ids(int | list[int]): 画像IDまたは画像IDのリスト

        Returns:
            None
        """
        ...

    def get(self, image_id: int) -> ImageEntry | None:
        """主キーで1件取得

        Args:
            image_id(int): 画像ID

        Returns:
            ImageEntry | None: 画像
        """
        ...

    def find_by_hashes(self, hash_values: ImageHash | list[ImageHash]) -> list[ImageEntry]:
        """ハッシュで1件取得

        内部でhash_valueをリストに変換してfind_by_hashesを呼び出す。
        実処理はfind_by_hashesで行う。

        Args:
            hash_value(ImageHash): ハッシュ

        Returns:
            ImageEntry | None: 画像
        """
        ...

    def update(self, entities: list[ImageEntry]) -> None:
        """複数の画像をまとめてUPDATE

        Args:
            entities(list[ImageEntry]): 複数の画像

        Returns:
            None
        """
        ...

    def contains(self, image_id: int) -> bool:
        """主キーが存在するか

        Args:
            image_id(int): 画像ID

        Returns:
            bool: 主キーが存在するか
        """
        ...
