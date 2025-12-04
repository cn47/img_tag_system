from common.registry import NestedRegistry, Registry


StorageAdapterRegistry = Registry("storage_adapter")
DatabaseAdapterRegistry = Registry("database_adapter")
TaggerAdapterRegistry = Registry("tagger_adapter")
RepositoryAdapterRegistry = NestedRegistry("repository_adapter")
