import duckdb
import pandas as pd

from application.repositories.debugging import DebuggableRepository
from application.repositories.images import ImagesRepository
from domain.entities.images import ImageEntry
from exceptions import DuplicateImageError, InfrastructureError


class DuckDBImagesRepository(ImagesRepository, DebuggableRepository):
    """imagesテーブルのリポジトリ"""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self.conn = conn

    def _row_to_entity(self, row: tuple) -> ImageEntry:
        (image_id, file_location, width, height, file_type, hash_value, added_at, updated_at) = row
        return ImageEntry(
            image_id=image_id,
            file_location=file_location,
            width=width,
            height=height,
            file_type=file_type,
            hash=hash_value,
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
            result = self.conn.execute(
                """
                INSERT INTO images (file_location, width, height, file_type, hash)
                SELECT file_location, width, height, file_type, hash FROM img_df
                RETURNING image_id
                """,
            ).fetchall()
            self.conn.unregister("img_df")
            return [row[0] for row in result]
        except duckdb.ConstraintException as e:
            if "Duplicate key" in str(e) and "violates unique constraint" in str(e):
                msg = "Duplicate hash detected during bulk insert"
                raise DuplicateImageError(msg) from e
            raise InfrastructureError(e) from e

    def update_file_location(self, image_id: int, file_location: str) -> None:
        self.conn.execute(
            """
            UPDATE images
                SET file_location = ?,
                    updated_at = CURRENT_TIMESTAMP
            WHERE image_id = ?
            """,
            (
                file_location,
                image_id,
            ),
        )

    def delete(self, image_id: int) -> None:
        self.conn.execute("DELETE FROM images WHERE image_id = ?", (image_id,))

    def get(self, image_id: int) -> ImageEntry | None:
        result = self.conn.execute(
            """
            SELECT * FROM images WHERE image_id = ?
            """,
            (image_id,),
        ).fetchone()
        return self._row_to_entity(result) if result else None

    def find_by_hash(self, hash_value: str) -> ImageEntry | None:
        if not hash_value:
            return None

        result = self.find_by_hashes([hash_value])
        return result[0] if result else None

    def find_by_hashes(self, hash_values: list[str]) -> list[ImageEntry]:
        if not hash_values:
            return []

        placeholders = ",".join(["?"] * len(hash_values))
        result = self.conn.execute(f"SELECT * FROM images WHERE hash IN ({placeholders})", hash_values).fetchall()  # noqa: S608
        return [self._row_to_entity(row) for row in result]

    def list_file_locations(self) -> list[tuple[int, str]]:
        result = self.conn.execute("SELECT image_id, file_location FROM images").fetchall()
        return result if result else []

    def exists(self, image_id: int) -> bool:
        result = self.conn.execute("SELECT COUNT(*) FROM images WHERE image_id = ?", (image_id,)).fetchone()
        return result[0] > 0 if result else False

    def count(self) -> int:
        result = self.conn.execute("SELECT COUNT(*) FROM images").fetchone()
        return result[0] if result else 0

    def list_all_as_df(self, limit: int = 20) -> pd.DataFrame:
        result = self.conn.execute(
            """SELECT * FROM images LIMIT ?""",
            (limit,),
        ).fetchdf()
        return result
