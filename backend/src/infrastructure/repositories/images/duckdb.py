import duckdb
import pandas as pd

from domain.entities.images import ImageEntry
from domain.exceptions import DuplicateImageError
from domain.repositories.debugging import DebuggableRepository
from domain.repositories.images import ImagesRepository
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from infrastructure.exceptions import InfrastructureError
from infrastructure.registry.adapter import RepositoryAdapterRegistry
from infrastructure.repositories.base.duckdb_base import BaseDuckDBRepository


@RepositoryAdapterRegistry.register("images", "duckdb")
class DuckDBImagesRepository(BaseDuckDBRepository, ImagesRepository, DebuggableRepository):
    """imagesテーブルのリポジトリ"""

    def __init__(self, database_file: str, table_name: str) -> None:
        super().__init__(database_file=database_file, table_name=table_name)

    def _row_to_entity(self, row: tuple) -> ImageEntry:
        (image_id, file_location, width, height, file_type, hash_value, file_size, added_at, updated_at) = row
        return ImageEntry(
            image_id=image_id,
            file_location=FileLocation(file_location),
            width=width,
            height=height,
            file_type=file_type,
            hash=ImageHash(hash_value),
            file_size=file_size,
            added_at=added_at,
            updated_at=updated_at,
        )

    def add(self, entries: ImageEntry | list[ImageEntry]) -> list[int]:
        entries = [entries] if isinstance(entries, ImageEntry) else entries
        return self._bulk_add(entries)

    def _bulk_add(self, entries: list[ImageEntry]) -> list[int]:
        """複数の画像をまとめてBULK INSERTして主キーのリストを返す

        Args:
            entries(list[ImageEntry]): 複数の画像

        Returns:
            list[int]: 主キーのリスト

        Raises:
            DuplicateImageError: 重複するハッシュが存在する場合
            InfrastructureError: インフラストラクチャエラー
        """
        if not entries:
            return []
        try:
            df = pd.DataFrame([entry.to_dict() for entry in entries])
            self.conn.register("img_df", df)
            _cols = "file_location, width, height, file_type, hash, file_size"
            q = f"INSERT INTO {self.table_name} ({_cols}) SELECT {_cols} FROM img_df RETURNING image_id"
            result = self.conn.execute(q).fetchall()
        except duckdb.ConstraintException as e:
            if "Duplicate key" in str(e) and "violates unique constraint" in str(e):
                msg = "Duplicate hash detected during bulk insert"
                raise DuplicateImageError(msg) from e
            raise InfrastructureError(e) from e
        finally:
            self.conn.unregister("img_df")

        return [row[0] for row in result]

    def remove(self, image_ids: int | list[int]) -> None:
        if not image_ids:
            raise ValueError("image_ids must be a list of integers and not empty")
        image_ids = [image_ids] if isinstance(image_ids, int) else image_ids

        q = f"DELETE FROM {self.table_name} WHERE image_id IN ({self.sql_placeholders(image_ids)})"
        self.conn.execute(q, image_ids)

    def get(self, image_id: int) -> ImageEntry | None:
        q = f"SELECT * FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,)).fetchone()
        return self._row_to_entity(result) if result else None

    def find_by_hashes(self, hash_values: ImageHash | list[ImageHash]) -> list[ImageEntry]:
        if not hash_values:
            return []
        hash_values = [hash_values] if isinstance(hash_values, ImageHash) else hash_values

        hash_strings = [str(hash_value) for hash_value in hash_values]
        q = f"SELECT * FROM {self.table_name} WHERE hash IN ({self.sql_placeholders(hash_strings)})"
        result = self.conn.execute(q, hash_strings).fetchall()
        return [self._row_to_entity(row) for row in result]

    def update(self, entities: list[ImageEntry]) -> None:
        if not entities:
            raise ValueError("entities must be a list of ImageEntry and not empty")
        entities = [entities] if isinstance(entities, ImageEntry) else entities

        df = pd.DataFrame([entry.to_dict() for entry in entities])
        self.conn.register("img_df", df)
        _cols = ["file_location", "width", "height", "file_type", "file_size"]
        _cols = ", ".join([f"{_c}=img_df.{_c}" for _c in _cols])
        try:
            q = f"""
            UPDATE {self.table_name} SET {_cols}, updated_at = CURRENT_TIMESTAMP
            FROM img_df
            WHERE {self.table_name}.image_id = img_df.image_id
            """
            self.conn.execute(q)
        finally:
            self.conn.unregister("img_df")

    def contains(self, image_id: int) -> bool:
        q = f"SELECT COUNT(*) FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,)).fetchone()
        return result[0] > 0 if result else False

    # ---- For Debugging ----
    def count(self) -> int:
        q = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self.conn.execute(q).fetchone()
        return result[0] if result else 0

    def list_all_as_df(self, limit: int = 20) -> pd.DataFrame:
        q = f"SELECT * FROM {self.table_name} LIMIT ?"
        result = self.conn.execute(q, (limit,)).fetchdf()
        return result
