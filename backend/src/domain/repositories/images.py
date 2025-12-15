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

    def insert(self, entries: ImageEntry | list[ImageEntry]) -> list[int]:
        """1件の画像または複数の画像をまとめてINSERTして主キーのリストを返す

        内部でentriesをリストに変換してBULK INSERTを呼び出す。

        Args:
            entries(ImageEntry | list[ImageEntry]): 1件の画像または複数の画像

        Returns:
            list[int]: 主キーのリスト

        Raises:
            DuplicateImageError: 重複するハッシュが存在する場合
            InfrastructureError: インフラストラクチャエラー
        """
        ...

    def update_file_location(self, image_id: int, file_location: FileLocation) -> None:
        """ファイルパスを更新

        Args:
            image_id(int): 画像ID
            file_location(FileLocation): ファイルパス

        """
        ...

    def delete(self, image_id: int) -> None:
        """主キーで削除

        Args:
            image_id(int): 画像ID

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

    def find_by_hash(self, hash_value: ImageHash) -> ImageEntry | None:
        """ハッシュで1件取得

        内部でhash_valueをリストに変換してfind_by_hashesを呼び出す。
        実処理はfind_by_hashesで行う。

        Args:
            hash_value(ImageHash): ハッシュ

        Returns:
            ImageEntry | None: 画像
        """
        ...

    def find_by_hashes(self, hash_values: list[ImageHash]) -> list[ImageEntry]:
        """ハッシュのリストで複数件取得

        Args:
            hash_values(list[ImageHash]): ハッシュのリスト

        Returns:
            list[ImageEntry]: 画像のリスト
        """
        ...

    def list_file_locations(self) -> list[tuple[int, FileLocation]]:
        """画像IDとファイルパスのペアリスト

        Args:
            None

        Returns:
            list[tuple[int, FileLocation]]: 画像IDとファイルパスのペアリスト
        """
        ...

    def exists(self, image_id: int) -> bool:
        """主キーが存在するか

        Args:
            image_id(int): 画像ID

        Returns:
            bool: 主キーが存在するか
        """
        ...
