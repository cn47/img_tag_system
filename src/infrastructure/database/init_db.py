from pathlib import Path

import duckdb


def initialize_database(db_file: str | Path, schema_file: str | Path, overwrite: bool = False):
    """DuckDBデータベースを初期化する

    既存のデータベースファイルが存在しない場合、新規に作成しスキーマを適用する。

    Args:
        db_file (str | Path): データベースファイルのパス
        schema_file (str | Path): スキーマSQLファイルのパス
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
