from dataclasses import dataclass
from pathlib import Path

from application.config.enums import DataBaseType, RepositoryType, StorageType, TaggerType
from application.config.registries import (
    DatabaseConfigRegistry,
    RepositoryConfigRegistry,
    StorageConfigRegistry,
    TaggerConfigRegistry,
)


# 増えてきたら分割する
# ----- Storage Config -----
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

    root_dir: str = Path(__file__).parents[3].resolve().as_posix()
    # root_dir: str = "data/storage/local"

    @property
    def adapter_key(self) -> str:
        return "local_file_system"


# ----- Database Config -----
@dataclass(frozen=True)
class DataBaseConfig:
    """データベース設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@DatabaseConfigRegistry.register("duckdb")
@dataclass(frozen=True)
class DuckDBConfig(DataBaseConfig):
    database_file: str = "data/database/images.duckdb"

    @property
    def adapter_key(self) -> str:
        return "duckdb"


# ----- Repository Config -----
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
    table_name: str = "images"

    @property
    def adapter_key(self) -> str:
        return "images"


@RepositoryConfigRegistry.register("model_tag")
@dataclass(frozen=True)
class ModelTagRepositoryConfig(RepositoryConfig):
    # 利用するモデルによってテーブル名を変える
    table_name: str

    @property
    def adapter_key(self) -> str:
        return "model_tag"


# ----- Tagger Config -----
@dataclass(frozen=True)
class TaggerModelConfig:
    """タグ付けモデルの設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@TaggerConfigRegistry.register("camie_v2")
@dataclass(frozen=True)
class CamieV2TaggerModelConfig(TaggerModelConfig):
    model_dir: str = "data/model/camie-tagger-v2"
    threshold: float = 0.0

    @property
    def tag_table_name(self) -> str:
        return "tags_camie_v2"

    @property
    def adapter_key(self) -> str:
        return "camie_v2"


# ----- App Config -----
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
