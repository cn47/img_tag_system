"""パス関連のユーティリティ関数"""

from pathlib import Path


def get_project_root() -> Path:
    """プロジェクトのルートディレクトリを返す"""
    return Path(__file__).parents[2].resolve()

