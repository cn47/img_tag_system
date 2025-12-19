from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def get_root() -> Path:
    """プロジェクトのルートディレクトリを取得"""
    try:
        return _find_root_by_marker(".git")
    except FileNotFoundError:
        return _find_root_by_marker("pyproject.toml")


def _find_root_by_marker(marker: str) -> Path:
    """探索ロジック"""
    current = Path(__file__).resolve().parent

    for parent in [current, *list(current.parents)]:
        if (parent / marker).exists():
            return parent

    raise FileNotFoundError(f"Marker '{marker}' not found.")
