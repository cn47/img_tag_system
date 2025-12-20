from dataclasses import dataclass, field

from common.path.project import get_root
from infrastructure.registry.config import StorageConfigRegistry


@dataclass(frozen=True)
class StorageConfig:
    """オブジェクトストレージの設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@StorageConfigRegistry.register("local")
@dataclass(frozen=True)
class LocalStorageConfig(StorageConfig):
    """ローカルストレージの設定"""

    root_dir: str = field(default_factory=lambda: str(get_root()))

    @property
    def adapter_key(self) -> str:
        return "local"
