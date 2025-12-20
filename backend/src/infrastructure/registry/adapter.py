from infrastructure.registry.core import NestedRegistry, Registry


StorageAdapterRegistry = NestedRegistry("storage_adapter")
# DatabaseAdapterRegistry = Registry("database_adapter") # TODO: 将来的に異なる実装が必要になった場合は、設定とレジストリを追加する。
TaggerAdapterRegistry = Registry("tagger_adapter")
RepositoryAdapterRegistry = NestedRegistry("repository_adapter")
