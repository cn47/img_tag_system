import os
import shutil

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

from application.storage.ports import StorageAccessor, StorageOperator
from infrastructure.registry.adapter import StorageAdapterRegistry


if TYPE_CHECKING:
    from infrastructure.configs.storage import LocalStorageConfig


@StorageAdapterRegistry.register("local", "accessor")
class LocalStorageAccessor(StorageAccessor):
    """Query操作"""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = str(root_dir)

    @classmethod
    def from_config(cls, config: "LocalStorageConfig") -> "LocalStorageAccessor":
        return cls(root_dir=str(config.root_dir))

    def _scan_fast(self, path: str) -> Generator[str, None, None]:
        """高速な再帰走査"""
        stack = [path]
        while stack:
            cur = stack.pop()
            with os.scandir(cur) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    # シンボリックリンク先は辿らない
                    elif entry.is_file(follow_symlinks=False) or entry.is_symlink():
                        yield entry.path

    def list_files(self, path: str | Path, recursive: bool = False) -> list[str]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError

        if p.is_file():
            return [str(p)]

        if recursive:
            return list(self._scan_fast(str(p)))

        with os.scandir(p) as it:
            return [entry.path for entry in it if entry.is_file(follow_symlinks=False) or entry.is_symlink()]

    def exists(self, path: str | Path, *, follow_symlinks: bool = True) -> bool:
        return Path(path).exists(follow_symlinks=follow_symlinks)

    def get_size(self, path: str | Path) -> int:
        return Path(path).stat().st_size

    def read_binary(self, path: str | Path) -> bytes:
        with Path(path).open("rb") as fp:
            return fp.read()

    def read_text(self, path: str | Path, encoding: str = "utf-8") -> str:
        with Path(path).open("r", encoding=encoding) as fp:
            return fp.read()

    def get_file_extension(self, path: str | Path) -> str:
        return Path(path).suffix.lower().lstrip(".")


@StorageAdapterRegistry.register("local", "operator")
class LocalStorageOperator(StorageOperator):
    """Command操作"""

    def __init__(self, root_dir: str | Path) -> None:
        self.root_dir = str(root_dir)

    @classmethod
    def from_config(cls, config: "LocalStorageConfig") -> "LocalStorageOperator":
        return cls(root_dir=str(config.root_dir))

    def copy(
        self, source: str | Path, destination: str | Path, overwrite: bool = False, create_parents: bool = True
    ) -> str:
        src, dest = Path(source), Path(destination)
        if not overwrite and dest.exists():
            raise FileExistsError(f"Destination exists: {dest}")

        # 移動元がファイルなのに、移動先が「既存のディレクトリ」なら上書きフラグがあっても止める
        if src.is_file() and dest.is_dir():
            raise IsADirectoryError(f"Cannot move file to existing directory: {dest}")

        if create_parents:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))
        return str(dest)

    def delete(self, path: str | Path, recursive: bool = False) -> None:
        p = Path(path)
        if not p.exists():
            return

        if p.is_dir():
            if recursive:
                shutil.rmtree(str(p))
            else:
                raise IsADirectoryError(f"Cannot delete directory without recursive=True: {p}")
        else:
            p.unlink()

    def move(
        self,
        source: str | Path,
        destination: str | Path,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> str:
        src, dest = Path(source), Path(destination)
        if not overwrite and dest.exists():
            raise FileExistsError(f"Destination exists: {dest}")

        # 移動元がファイルなのに、移動先が「既存のディレクトリ」なら上書きフラグがあっても止める
        if src.is_file() and dest.is_dir():
            raise IsADirectoryError(f"Cannot move file to existing directory: {dest}")

        if create_parents:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return str(dest)
