from typing import Protocol


class SupportedRepository(Protocol):
    """サポートされるリポジトリ"""

    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class UnitOfWorkProtocol(Protocol):
    """Unit of Work

    リポジトリ操作において整合性を保つためのインターフェース

    """

    def __getitem__(self, key: str) -> SupportedRepository:
        """サポートされるリポジトリを取得"""
        ...

    def subset(self, keys: list[str]) -> "UnitOfWorkProtocol":
        """指定されたキーのサブセットをUnit of Workとして取得"""
        ...

    def _commit(self) -> None:
        """トランザクションをコミット"""
        ...

    def _rollback(self) -> None:
        """トランザクションをロールバック"""
        ...

    def __enter__(self) -> "UnitOfWorkProtocol":
        """コンテキストマネージャーの開始"""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャーの終了

        例外が発生しなかった場合はcommit、発生した場合はrollback
        """
        ...
