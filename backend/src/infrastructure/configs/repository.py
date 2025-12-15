from dataclasses import dataclass

from infrastructure.configs.database import DataBaseConfig
from infrastructure.registry.config import RepositoryConfigRegistry


@dataclass(frozen=True)
class RepositoryConfig:
    """リポジトリ設定の基底インターフェースクラス"""

    database: DataBaseConfig

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class RepositoryConfigGroup:
    """リポジトリ設定のグループ"""

    images: RepositoryConfig
    model_tag: RepositoryConfig

    def __getitem__(self, key: str) -> RepositoryConfig:
        return getattr(self, key)


@RepositoryConfigRegistry.register("images")
@dataclass(frozen=True)
class ImagesRepositoryConfig(RepositoryConfig):
    """画像メタデータRepository"""

    table_name: str = "images"

    @property
    def adapter_key(self) -> str:
        return "images"


@RepositoryConfigRegistry.register("model_tag")
@dataclass(frozen=True)
class ModelTagRepositoryConfig(RepositoryConfig):
    """モデルタグRepository"""

    # 利用するモデルによってテーブル名を変える
    table_name: str

    @property
    def adapter_key(self) -> str:
        return "model_tag"

