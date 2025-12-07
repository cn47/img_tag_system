import duckdb
import pandas as pd

from application.config.app_config import ImagesRepositoryConfig
from common.exceptions import DuplicateImageError, InfrastructureError
from domain.entities.images import ImageEntry
from domain.repositories.debugging import DebuggableRepository
from domain.repositories.images import ImagesRepository
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from infrastructure.registries import RepositoryAdapterRegistry
from infrastructure.repositories.base.duckdb_base import BaseDuckDBRepository


@RepositoryAdapterRegistry.register("images", "duckdb")
class DuckDBImagesRepository(BaseDuckDBRepository, ImagesRepository, DebuggableRepository):
    """imagesテーブルのリポジトリ"""

    def __init__(self, database_file: str, table_name: str) -> None:
        super().__init__(database_file=database_file, table_name=table_name)

    @classmethod
    def from_config(cls, config: ImagesRepositoryConfig) -> "DuckDBImagesRepository":
        return cls(database_file=config.database.database_file, table_name=config.table_name)

    def _row_to_entity(self, row: tuple) -> ImageEntry:
        (image_id, file_location, width, height, file_type, hash_value, added_at, updated_at) = row
        return ImageEntry(
            image_id=image_id,
            file_location=FileLocation(file_location),
            width=width,
            height=height,
            file_type=file_type,
            hash=ImageHash(hash_value),
            added_at=added_at,
            updated_at=updated_at,
        )

    def insert(self, entries: ImageEntry | list[ImageEntry]) -> list[int]:
        entries = [entries] if isinstance(entries, ImageEntry) else entries
        return self._bulk_insert(entries)

    def _bulk_insert(self, entries: list[ImageEntry]) -> list[int]:
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
            _cols = "file_location, width, height, file_type, hash"
            q = f"INSERT INTO {self.table_name} ({_cols}) SELECT {_cols} FROM img_df RETURNING image_id"
            result = self.conn.execute(q).fetchall()
            self.conn.unregister("img_df")
            return [row[0] for row in result]
        except duckdb.ConstraintException as e:
            if "Duplicate key" in str(e) and "violates unique constraint" in str(e):
                msg = "Duplicate hash detected during bulk insert"
                raise DuplicateImageError(msg) from e
            raise InfrastructureError(e) from e

    def update_file_location(self, image_id: int, file_location: FileLocation) -> None:
        q = f"UPDATE {self.table_name} SET file_location = ?, updated_at = CURRENT_TIMESTAMP WHERE image_id = ?"
        self.conn.execute(q, (str(file_location), image_id))

    def delete(self, image_id: int) -> None:
        q = f"DELETE FROM {self.table_name} WHERE image_id = ?"
        self.conn.execute(q, (image_id,))

    def get(self, image_id: int) -> ImageEntry | None:
        q = f"SELECT * FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,)).fetchone()
        return self._row_to_entity(result) if result else None

    def find_by_hash(self, hash_value: ImageHash) -> ImageEntry | None:
        result = self.find_by_hashes([hash_value])
        return result[0] if result else None

    def find_by_hashes(self, hash_values: list[ImageHash]) -> list[ImageEntry]:
        if not hash_values:
            return []

        hash_strings = [str(hash_value) for hash_value in hash_values]
        q = f"SELECT * FROM {self.table_name} WHERE hash IN ({self.sql_placeholders(hash_strings)})"
        result = self.conn.execute(q, hash_strings).fetchall()
        return [self._row_to_entity(row) for row in result]

    def list_file_locations(self) -> list[tuple[int, FileLocation]]:
        q = f"SELECT image_id, file_location FROM {self.table_name}"
        result = self.conn.execute(q).fetchall()
        if not result:
            return []
        return [(image_id, FileLocation(file_location)) for image_id, file_location in result]

    def exists(self, image_id: int) -> bool:
        q = f"SELECT COUNT(*) FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,)).fetchone()
        return result[0] > 0 if result else False

    def count(self) -> int:
        q = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self.conn.execute(q).fetchone()
        return result[0] if result else 0

    def list_all_as_df(self, limit: int = 20) -> pd.DataFrame:
        q = f"SELECT * FROM {self.table_name} LIMIT ?"
        result = self.conn.execute(q, (limit,)).fetchdf()
        return result
