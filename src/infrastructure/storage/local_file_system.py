from pathlib import Path


class LocalFileSystem:
    """ローカルファイルシステム"""

    def __init__(self) -> None:
        """LocalFileSystemを初期化する"""
        self.base_dir = Path(".")

    def get_files(self, dir_path: str | Path, recursive: bool = False) -> list[str]:
        """ディレクトリ内のすべてのファイルパスを取得する"""
        _path = Path(dir_path).rglob("*") if recursive else Path(dir_path).glob("*")
        return [str(p) for p in _path if p.is_file()]
