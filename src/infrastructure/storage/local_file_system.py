import os

from collections.abc import Generator
from pathlib import Path

from application.config.app_config import LocalFileSystemConfig
from infrastructure.registries import StorageAdapterRegistry


@StorageAdapterRegistry.register("local_file_system")
class LocalFileSystem:
    """ローカルファイルシステム"""

    def __init__(self, root_dir: str) -> None:
        self.root_dir = root_dir

    @classmethod
    def from_config(cls, config: LocalFileSystemConfig) -> "LocalFileSystem":
        return cls(root_dir=config.root_dir)

    @staticmethod
    def _scan_fast(path: Path) -> Generator[Path, None, None]:
        """高速な再帰走査"""
        stack = [path]
        while stack:
            cur = stack.pop()
            with os.scandir(cur) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    # シンボリックリンク先は辿らない
                    elif entry.is_file(follow_symlinks=False) or entry.is_symlink():
                        yield Path(entry.path)

    @classmethod
    def list_files(cls, path: str | Path, recursive: bool = False) -> list[str]:
        """ファイルを走査してパスのリストを返す

        Args:
            path(str | Path): パス
            recursive(bool): 再帰的に走査するかどうか。True の場合はディレクトリも再帰的に走査する。
                False の場合はディレクトリは走査しない。デフォルトは False。

        Returns:
            list[str]: ファイルのパスのリスト
        """
        p = Path(path)

        if not p.exists():
            raise FileNotFoundError

        if p.is_file():
            return [str(p)]

        if p.is_dir():
            if recursive:
                return [str(x) for x in cls._scan_fast(p)]

            with os.scandir(p) as it:
                return [str(Path(e.path)) for e in it if e.is_file(follow_symlinks=False) or e.is_symlink()]

        msg = f"Input not file or directory: {p}"
        raise ValueError(msg)
