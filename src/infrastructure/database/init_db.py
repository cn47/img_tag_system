from pathlib import Path

import duckdb

from common.path_utils import get_project_root


DEFAULT_DB_FILE = get_project_root() / "data" / "database" / "images.duckdb"
DEFAULT_SCHEMA_FILE = get_project_root() / "src" / "infrastructure" / "database" / "schema.sql"


def initialize_database(
    db_file: str | Path = DEFAULT_DB_FILE,
    schema_file: str | Path = DEFAULT_SCHEMA_FILE,
    overwrite: bool = False,
) -> None:
    """DuckDBデータベースを初期化する

    既存のデータベースファイルが存在しない場合、新規に作成しスキーマを適用する。

    Args:
        db_file (str | Path): データベースファイルのパス (デフォルト: data/database/images.duckdb)
        schema_file (str | Path): スキーマSQLファイルのパス (デフォルト: src/infrastructure/database/schema.sql)
        overwrite (bool): 既存のデータベースファイルが存在する場合に上書きするかどうか
    """
    db_file = Path(db_file)
    schema_file = Path(schema_file)

    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with schema_file.open("r", encoding="utf-8") as f:
        schema_sql = f.read()

    if overwrite and db_file.exists():
        db_file.unlink()

    with duckdb.connect(database=str(db_file)) as conn:
        conn.execute(schema_sql)

    print(f"Database initialized at: {db_file}")
