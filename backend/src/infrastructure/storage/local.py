import os
import shutil

from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

from infrastructure.storage.base import StoragePath


if TYPE_CHECKING:
    from domain.storage.path import StoragePath as StoragePathProtocol


class LocalStoragePath(Path, StoragePath):
    """ローカルファイルシステムのパス

    Pathを継承

    """

    def __new__(cls, *args: str | Path, **kwargs) -> "LocalStoragePath":
        return super().__new__(cls, *args, **kwargs)

    def as_uri(self) -> str:
        """パスをURI形式に変換する

        Returns:
            str: URI形式のパス

        Note:
            Windowsのパスは一旦想定外として、Unixのパスを返す
        """
        return f"file://{self.absolute()}"

    @staticmethod
    def _scan_fast(path: str) -> Generator[str, None, None]:
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

    def list_files(self, recursive: bool = False) -> list["LocalStoragePath"]:
        if not self.exists():
            raise FileNotFoundError

        if self.is_file():
            return [self]

        if recursive:
            return [LocalStoragePath(path) for path in self._scan_fast(str(self))]

        with os.scandir(self) as it:
            return [
                LocalStoragePath(entry.path)
                for entry in it
                if entry.is_file(follow_symlinks=False) or entry.is_symlink()
            ]

    def exists(self, *, follow_symlinks: bool = True) -> bool:
        # Pathlib
        return super().exists(follow_symlinks=follow_symlinks)

    def get_size(self) -> int:
        """ファイルサイズ（バイト数）を取得する"""
        return super().stat().st_size

    def copy(
        self,
        destination: "StoragePathProtocol",
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> "LocalStoragePath":
        dest = LocalStoragePath(str(destination))
        if not overwrite and dest.exists():
            raise FileExistsError(f"Destination exists: {dest}")

        # 移動元がファイルなのに、移動先が「既存のディレクトリ」なら上書きフラグがあっても止める
        if self.is_file() and dest.is_dir():
            raise IsADirectoryError(f"Cannot move file to existing directory: {dest}")

        if create_parents:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(self), str(dest))
        return dest

    def delete(self, recursive: bool = False) -> None:
        if not self.exists():
            return

        if self.is_dir():
            if recursive:
                shutil.rmtree(str(self))
            else:
                raise IsADirectoryError(f"Cannot delete directory without recursive=True: {self}")
        else:
            self.unlink()

    def move(
        self,
        destination: "StoragePathProtocol",
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> "LocalStoragePath":
        dest = LocalStoragePath(str(destination))
        if not overwrite and dest.exists():
            raise FileExistsError(f"Destination exists: {dest}")

        # 移動元がファイルなのに、移動先が「既存のディレクトリ」なら上書きフラグがあっても止める
        if self.is_file() and dest.is_dir():
            raise IsADirectoryError(f"Cannot move file to existing directory: {dest}")

        if create_parents:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self), str(dest))
        return dest
