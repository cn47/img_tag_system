import itertools

import duckdb
import pandas as pd

from application.repositories.debugging import DebuggableRepository
from application.repositories.model_tag import ModelTagRepository
from domain.entities.model_tag import ModelTagEntries, ModelTagEntry
from domain.model_name import ModelName
from exceptions import ImageNotFoundError, InfrastructureError


class DuckDBModelTagRepository(ModelTagRepository, DebuggableRepository):
    """DuckDBを使用したModelTagRepositoryの実装"""

    def __init__(self, conn: duckdb.DuckDBPyConnection, model_name: ModelName) -> None:
        self.conn = conn
        self.model_name = model_name.value

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
            self.conn.execute(
                f"""
                INSERT OR REPLACE INTO tags_{self.model_name} (image_id, category, tag, score, archived)
                SELECT image_id, category, tag, score, archived FROM tag_df
                """,  # noqa: S608
            )
            self.conn.unregister("tag_df")
        except duckdb.ConstraintException as e:
            if "Violates foreign key constraint" in str(e) and "does not exist in the referenced table" in str(e):
                msg = "Image ID not found"
                raise ImageNotFoundError(msg) from e
            raise InfrastructureError(e) from e

    def list_by_image_id(self, image_id: int) -> ModelTagEntries:
        result = self.conn.execute(
            f"""
            SELECT * FROM tags_{self.model_name} WHERE image_id = ?
            """,  # noqa: S608
            (image_id,),
        ).fetchall()
        return (
            ModelTagEntries(entries=[self._row_to_entity(row) for row in result])
            if result
            else ModelTagEntries(entries=[])
        )

    def find_tagged_image_ids(self, image_ids: list[int]) -> set[int]:
        if not image_ids:
            return set()

        placeholders = ",".join(["?"] * len(image_ids))
        result = self.conn.execute(
            f"""SELECT DISTINCT image_id FROM tags_{self.model_name} WHERE image_id IN ({placeholders})""",  # noqa: S608
        ).fetchall()
        return {int(row[0]) for row in result}

    def delete_all_by_image_id(self, image_id: int) -> int:
        result = self.conn.execute(
            f"""
            DELETE FROM tags_{self.model_name} WHERE image_id = ?
            """,  # noqa: S608
            (image_id,),
        )
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
        result = self.conn.execute(
            f"""
            UPDATE tags_{self.model_name}
            SET archived = TRUE
            FROM tag_df
            WHERE tags_{self.model_name}.image_id = tag_df.image_id
              AND tags_{self.model_name}.category = tag_df.category
              AND tags_{self.model_name}.tag = tag_df.tag
            """,  # noqa: S608
        )
        self.conn.unregister("tag_df")
        return result.rowcount

    def count(self) -> int:
        result = self.conn.execute(f"SELECT COUNT(*) FROM tags_{self.model_name}").fetchone()  # noqa: S608
        return result[0] if result else 0

    def list_all_as_df(self, limit: int = 20) -> pd.DataFrame:
        result = self.conn.execute(
            f"""SELECT * FROM tags_{self.model_name} LIMIT ?""",  # noqa: S608
            (limit,),
        ).fetchdf()
        return result
