import importlib

from types import ModuleType
from typing import TYPE_CHECKING, TypeGuard

from infrastructure.registry.adapter import (
    RepositoryAdapterRegistry,
    StorageAdapterRegistry,
    TaggerAdapterRegistry,
)


if TYPE_CHECKING:
    from infrastructure.composition.runtime_config import RuntimeConfig
    from infrastructure.configs.database import DataBaseConfig, DuckDBConfig


class RuntimeFactory:
    """Runtimeで使用するオブジェクトを作成するためのファクトリ

    設定に応じて、Storage, Database, Repository, Taggerを作成する。

    Args:
        config(RuntimeConfig): ランタイム設定

    Examples:
        >>> factory = RuntimeFactory(config)
        >>> storage = factory.create_storage()
        >>> database = factory.create_database()
        >>> repository = factory.create_repository("model_tag")
        >>> tagger = factory.create_tagger()
    """

    def __init__(self, config: "RuntimeConfig"):
        self.config = config

    @staticmethod
    def _load_adapter(module_path: str) -> ModuleType:
        """モジュールを動的に読み込む

        Registryに登録されているクラスを動的に読み込む

        Args:
            module_path(str): モジュールのパス

        Returns:
            type: モジュールのクラス
        """
        return importlib.import_module(module_path)

    def create_storage(self):
        config = self.config.storage
        module_path = f"infrastructure.storage.{config.adapter_key}"

        self._load_adapter(module_path)

        cls = StorageAdapterRegistry[config.adapter_key]

        return cls.from_config(config)

    def _is_duckdb_config(self, config: "DataBaseConfig") -> TypeGuard["DuckDBConfig"]:
        return config.adapter_key == "duckdb"

    def create_database(self):
        """データベース

        NOTE: 現状はDuckDBのみ対応している。
        将来的に異なる実装が必要になった場合は、設定とレジストリを追加する。
        """
        config = self.config.database
        if self._is_duckdb_config(config):
            import duckdb

            return duckdb.connect(config.database_file)
        else:
            raise ValueError(f"Unsupported database adapter: {config.adapter_key}")

    def create_repository(self, repo_name: str):
        """リポジトリ"""
        config = self.config.repository[repo_name]
        module_path = f"infrastructure.repositories.{config.adapter_key}.{config.database.adapter_key}"

        self._load_adapter(module_path)

        cls = RepositoryAdapterRegistry.get(config.adapter_key, config.database.adapter_key)

        return cls.from_config(config)

    def create_unit_of_work(self):
        """Unit of Work

        NOTE: commit, rollbackメソッドを持つリポジトリならバックエンドDBを問わず使用できる。
        DBの種類に応じて、異なるUnit of Work実装が必要になった場合は、ここで切り替える。
        """
        from infrastructure.repositories.unit_of_work import UnitOfWork

        repos = {repo_name: self.create_repository(repo_name) for repo_name in self.config.repository.__dict__}

        return UnitOfWork(repos)

    def create_tagger(self):
        """タグ付けモデル"""
        config = self.config.tagger
        module_path = f"infrastructure.tagger.{config.adapter_key}"

        self._load_adapter(module_path)

        cls = TaggerAdapterRegistry[config.adapter_key]

        return cls.from_config(config)

    def create_image_loader(self):
        """画像ローダー

        NOTE: 現状は設定不要で、常にPILImageLoaderを使用する。
        将来的に異なる実装が必要になった場合は、設定とレジストリを追加する。
        """
        from infrastructure.services.image_loader import PILImageLoader

        return PILImageLoader()
