from pathlib import Path


class LocalFileSystem:
    """ローカルファイルシステム"""

    def __init__(self) -> None:
        """LocalFileSystemを初期化する"""

    def list_files(self, path: str | Path, recursive: bool = False) -> list[str]:
        """ディレクトリ内のすべてのファイルパスをリストで取得する"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError

        if p.is_file():
            return [str(p)]

        if p.is_dir():
            _path = p.rglob("*") if recursive else p.glob("*")
            return [str(p) for p in _path if p.is_file()]

        msg = f"input path is not a file or directory: {p}"
        raise ValueError(msg)
