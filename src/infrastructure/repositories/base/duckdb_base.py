from pathlib import Path

import duckdb

from application.configs.repository import RepositoryConfig


class BaseDuckDBRepository:
    """DuckDB基底リポジトリ"""

    def __init__(self, database_file: str | Path, table_name: str) -> None:
        self._conn = duckdb.connect(str(database_file))
        self._database_file = Path(database_file)
        self._table_name = table_name

    @classmethod
    def from_config(cls, config: RepositoryConfig) -> "BaseDuckDBRepository":
        return cls(database_file=config.database.database_file, table_name=config.table_name)

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        return self._conn

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    @property
    def database_file(self) -> Path:
        return self._database_file

    @property
    def table_name(self) -> str:
        return self._table_name

    def sql_placeholders(self, values: list | tuple | set) -> str:
        """list, tuple, setを?で囲んだ文字列に変換する"""
        if not isinstance(values, (list, tuple, set)):
            raise TypeError("values must be a list, tuple, or set")

        return ",".join(["?"] * len(values))
