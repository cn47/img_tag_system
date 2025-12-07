from dataclasses import dataclass

from application.configs.database import DataBaseConfig
from application.configs.repository import RepositoryConfigGroup
from application.configs.storage import StorageConfig
from application.configs.tagger import TaggerModelConfig
from application.system.enums import DataBaseType, RepositoryType, StorageType, TaggerType
from application.system.registries import (
    DatabaseConfigRegistry,
    RepositoryConfigRegistry,
    StorageConfigRegistry,
    TaggerConfigRegistry,
)


@dataclass(frozen=True)
class AppConfig:
    """アプリケーションの設定"""

    storage: StorageConfig
    database: DataBaseConfig
    repository: RepositoryConfigGroup
    tagger: TaggerModelConfig

    @staticmethod
    def build(
        storage_type: StorageType,
        database_type: DataBaseType,
        tagger_type: TaggerType,
    ) -> "AppConfig":
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

        return AppConfig(
            storage=storage,
            database=database,
            repository=repos,
            tagger=tagger,
        )


default_config = AppConfig.build(
    storage_type=StorageType.LOCAL,
    database_type=DataBaseType.DUCKDB,
    tagger_type=TaggerType.CAMIE_V2,
)
