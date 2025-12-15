from dataclasses import dataclass

from infrastructure.composition.enums import DataBaseType, RepositoryType, StorageType, TaggerType
from infrastructure.configs.database import DataBaseConfig
from infrastructure.configs.repository import RepositoryConfigGroup
from infrastructure.configs.storage import StorageConfig
from infrastructure.configs.tagger import TaggerModelConfig
from infrastructure.registry.config import (
    DatabaseConfigRegistry,
    RepositoryConfigRegistry,
    StorageConfigRegistry,
    TaggerConfigRegistry,
)


@dataclass(frozen=True)
class RuntimeConfig:
    """ランタイム設定

    RuntimeFactoryで使用する技術実装の選択と設定を保持する。
    """

    storage: StorageConfig
    database: DataBaseConfig
    repository: RepositoryConfigGroup
    tagger: TaggerModelConfig

    @staticmethod
    def build(
        storage_type: StorageType,
        database_type: DataBaseType,
        tagger_type: TaggerType,
    ) -> "RuntimeConfig":
        storage = StorageConfigRegistry(storage_type.value)
        database = DatabaseConfigRegistry(database_type.value)
        tagger = TaggerConfigRegistry(tagger_type.value)

        repos = RepositoryConfigGroup(
            images=RepositoryConfigRegistry(
                RepositoryType.IMAGES.value,
                database=database,
            ),
            model_tag=RepositoryConfigRegistry(
                RepositoryType.MODEL_TAG.value,
                database=database,
                table_name=tagger.tag_table_name,
            ),
        )

        return RuntimeConfig(
            storage=storage,
            database=database,
            repository=repos,
            tagger=tagger,
        )
