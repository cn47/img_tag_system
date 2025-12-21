import duckdb

from application.storage.ports import Storage


def initialize_database(storage: Storage, db_file: str, schema_file: str, overwrite: bool = False) -> None:
    """DuckDBデータベースを初期化する

    既存のデータベースファイルが存在しない場合、新規に作成しスキーマを適用する。

    Args:
        storage (Storage): ストレージ
        db_file (str): データベースファイルのパス
        schema_file (str): スキーマSQLファイルのパス
        overwrite (bool): 既存のデータベースファイルが存在する場合に上書きするかどうか
    """
    if not storage.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    schema_sql = storage.read_text(schema_file)

    if overwrite and storage.exists(db_file):
        storage.delete(db_file)

    with duckdb.connect(database=db_file) as conn:
        conn.execute(schema_sql)

    print(f"Database initialized at: {db_file}")
