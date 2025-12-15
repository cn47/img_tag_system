from dataclasses import dataclass, field
from pathlib import Path

from common.path_utils import get_project_root
from infrastructure.registry.config import StorageConfigRegistry


@dataclass(frozen=True)
class StorageConfig:
    """オブジェクトストレージの設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@StorageConfigRegistry.register("local")
@dataclass(frozen=True)
class LocalFileSystemConfig(StorageConfig):
    """ローカルファイルシステムの設定"""

    root_dir: Path = field(default_factory=get_project_root)
    # root_dir: Path = Path("data/storage/local")

    @property
    def adapter_key(self) -> str:
        return "local_file_system"

