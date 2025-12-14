import itertools

import pandas as pd

from duckdb import ConstraintException

from common.exceptions import ImageNotFoundError, InfrastructureError
from domain.entities.model_tag import ModelTagEntries, ModelTagEntry
from domain.repositories.debugging import DebuggableRepository
from domain.repositories.model_tag import ModelTagRepository
from infrastructure.registry.adapter import RepositoryAdapterRegistry
from infrastructure.repositories.base.duckdb_base import BaseDuckDBRepository


@RepositoryAdapterRegistry.register("model_tag", "duckdb")
class DuckDBModelTagRepository(BaseDuckDBRepository, ModelTagRepository, DebuggableRepository):
    """DuckDBを使用したModelTagRepositoryの実装"""

    def __init__(self, database_file: str, table_name: str) -> None:
        super().__init__(database_file=database_file, table_name=table_name)

    def _row_to_entity(self, row: tuple) -> ModelTagEntry:
        (image_id, category, tag, score, archived) = row
        return ModelTagEntry(
            image_id=image_id,
            category=category,
            tag=tag,
            score=score,
            archived=archived,
        )

    def insert(self, entries: ModelTagEntries | list[ModelTagEntries]) -> None:
        entries = [entries] if isinstance(entries, ModelTagEntries) else entries
        return self._bulk_insert(entries)

    def _bulk_insert(self, entries: list[ModelTagEntries]) -> None:
        """複数の画像に対する複数タグをまとめてBULK INSERT

        Args:
            entries(list[ModelTagEntries]): 複数の画像に対する複数タグ

        Returns:
            None

        Raises:
            ImageNotFoundError: 画像IDが存在しない場合
            InfrastructureError: インフラストラクチャエラー
        """
        if not entries:
            return

        try:
            flatten_entries = list(itertools.chain.from_iterable([entry.to_dict_list() for entry in entries]))
            tag_df = pd.DataFrame(flatten_entries)
            self.conn.register("tag_df", tag_df)
            _cols = "image_id, category, tag, score, archived"
            q = f"INSERT OR REPLACE INTO {self.table_name} ({_cols}) SELECT {_cols} FROM tag_df"
            self.conn.execute(q)
            self.conn.unregister("tag_df")
        except ConstraintException as e:
            if "Violates foreign key constraint" in str(e) and "does not exist in the referenced table" in str(e):
                msg = "Image ID not found"
                raise ImageNotFoundError(msg) from e
            raise InfrastructureError(e) from e

    def list_by_image_id(self, image_id: int) -> ModelTagEntries:
        q = f"SELECT * FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,)).fetchall()
        return (
            ModelTagEntries(entries=[self._row_to_entity(row) for row in result])
            if result
            else ModelTagEntries(entries=[])
        )

    def find_tagged_image_ids(self, image_ids: list[int]) -> set[int]:
        if not image_ids:
            return set()

        q = f"SELECT DISTINCT image_id FROM {self.table_name} WHERE image_id IN ({self.sql_placeholders(image_ids)})"
        result = self.conn.execute(q, image_ids).fetchall()
        return {int(row[0]) for row in result}

    def delete_all_by_image_id(self, image_id: int) -> int:
        q = f"DELETE FROM {self.table_name} WHERE image_id = ?"
        result = self.conn.execute(q, (image_id,))
        return result.rowcount

    def archive(self, image_id: int, category: str, tag: str) -> int:
        return self.archive_many(
            ModelTagEntries(
                entries=[
                    ModelTagEntry(
                        image_id=image_id,
                        category=category,
                        tag=tag,
                        score=0.0,  # score is not used for archiving
                        archived=True,
                    ),
                ],
            ),
        )

    def archive_many(self, entries: ModelTagEntries) -> int:
        if not entries.entries:
            return 0

        tag_df = pd.DataFrame(entries.to_dict_list())
        self.conn.register("tag_df", tag_df)
        q = f"""
            UPDATE {self.table_name}
            SET archived = TRUE
            FROM tag_df
            WHERE {self.table_name}.image_id = tag_df.image_id
              AND {self.table_name}.category = tag_df.category
              AND {self.table_name}.tag = tag_df.tag
        """
        result = self.conn.execute(q)
        self.conn.unregister("tag_df")
        return result.rowcount

    def count(self) -> int:
        q = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self.conn.execute(q).fetchone()
        return result[0] if result else 0

    def list_all_as_df(self, limit: int = 20) -> pd.DataFrame:
        q = f"SELECT * FROM {self.table_name} LIMIT ?"
        result = self.conn.execute(q, (limit,)).fetchdf()
        return result
