import importlib

from application.config.app_config import AppConfig
from infrastructure.registries import (
    DatabaseAdapterRegistry,
    RepositoryAdapterRegistry,
    StorageAdapterRegistry,
    TaggerAdapterRegistry,
)


class RuntimeFactory:
    """Runtimeで使用するオブジェクトを作成するためのファクトリ

    設定に応じて、Storage, Database, Repository, Taggerを作成する。

    Args:
        config(AppConfig): アプリケーションの設定

    Examples:
        >>> factory = RuntimeFactory(config)
        >>> storage = factory.create_storage()
        >>> database = factory.create_database()
        >>> repository = factory.create_repository("model_tag")
        >>> tagger = factory.create_tagger()
    """

    def __init__(self, config: AppConfig):
        self.config = config

    @staticmethod
    def _load_adapter(module_path: str) -> type:
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

    def create_database(self):
        config = self.config.database
        module_path = f"infrastructure.database.{config.adapter_key}"

        self._load_adapter(module_path)

        cls = DatabaseAdapterRegistry[config.adapter_key]

        return cls.from_config(config)

    def create_repository(self, repo_name: str):
        config = self.config.repository[repo_name]
        module_path = f"infrastructure.repositories.{config.adapter_key}.{config.database.adapter_key}"

        self._load_adapter(module_path)

        cls = RepositoryAdapterRegistry.get(config.adapter_key, config.database.adapter_key)

        return cls.from_config(config)

    def create_tagger(self):
        config = self.config.tagger
        module_path = f"infrastructure.tagger.{config.adapter_key}"

        self._load_adapter(module_path)

        cls = TaggerAdapterRegistry[config.adapter_key]

        return cls.from_config(config)
