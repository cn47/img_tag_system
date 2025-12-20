from application.storage.ports import Storage as StoragePort
from application.storage.ports import StorageAccessor, StorageOperator


class Storage(StoragePort):
    """ストレージクライアント"""

    def __init__(self, accessor: StorageAccessor, operator: StorageOperator) -> None:
        self._accessor = accessor
        self._operator = operator
        self.root_dir = accessor.root_dir

    # --- query operations(side-effect free) ---
    def list_files(self, path: str, recursive: bool = False) -> list[str]:
        return self._accessor.list_files(path, recursive)

    def exists(self, path: str, *, follow_symlinks: bool = True) -> bool:
        return self._accessor.exists(path, follow_symlinks=follow_symlinks)

    def get_size(self, path: str) -> int:
        return self._accessor.get_size(path)

    def read_binary(self, path: str) -> bytes:
        return self._accessor.read_binary(path)

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        return self._accessor.read_text(path, encoding)

    def get_file_extension(self, path: str) -> str:
        return self._accessor.get_file_extension(path)

    # --- command operations(side-effect) ---
    def copy(self, source: str, destination: str, overwrite: bool = False, create_parents: bool = True) -> str:
        return self._operator.copy(source, destination, overwrite, create_parents)

    def delete(self, path: str, recursive: bool = False) -> None:
        return self._operator.delete(path, recursive)

    def move(self, source: str, destination: str, overwrite: bool = False, create_parents: bool = True) -> str:
        return self._operator.move(source, destination, overwrite, create_parents)
