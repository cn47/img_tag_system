from typing import Protocol


class StorageAccessor(Protocol):
    """ストレージアクセサー(Query操作)"""

    def list_files(self, path: str, recursive: bool = False) -> list[str]: ...

    def exists(self, path: str, *, follow_symlinks: bool = True) -> bool: ...

    def get_size(self, path: str) -> int: ...

    def read_binary(self, path: str) -> bytes: ...

    def read_text(self, path: str, encoding: str = "utf-8") -> str: ...

    def get_file_extension(self, path: str) -> str: ...


class StorageOperator(Protocol):
    """ストレージオペレーター(Command操作)"""

    def copy(self, source: str, destination: str, overwrite: bool = False, create_parents: bool = True) -> str: ...

    def delete(self, path: str, recursive: bool = False) -> None: ...

    def move(self, source: str, destination: str, overwrite: bool = False, create_parents: bool = True) -> str: ...


class Storage(StorageAccessor, StorageOperator):
    """ストレージ"""
