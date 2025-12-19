from dataclasses import dataclass, field
from pathlib import Path

from common.path.project import get_root
from infrastructure.registry.config import DatabaseConfigRegistry


@dataclass(frozen=True)
class DataBaseConfig:
    """データベース設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@DatabaseConfigRegistry.register("duckdb")
@dataclass(frozen=True)
class DuckDBConfig(DataBaseConfig):
    """DuckDB設定"""

    database_file: Path = field(default_factory=lambda: get_root() / "data" / "database" / "images.duckdb")

    @property
    def adapter_key(self) -> str:
        return "duckdb"
