import duckdb


class BaseDuckDBRepository:
    """DuckDB基底リポジトリ"""

    def __init__(self, database_file: str, table_name: str) -> None:
        self._conn = duckdb.connect(database_file)
        self._database_file = database_file
        self._table_name = table_name

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        return self._conn

    @property
    def database_file(self) -> str:
        return self._database_file

    @property
    def table_name(self) -> str:
        return self._table_name

    def sql_placeholders(self, values: list | tuple | set) -> str:
        """list, tuple, setを?で囲んだ文字列に変換する"""
        if not isinstance(values, (list, tuple, set)):
            raise TypeError("values must be a list, tuple, or set")

        return ",".join(["?"] * len(values))
