from domain.storage.path import StoragePath as StoragePathProtocol


class StoragePath(StoragePathProtocol):
    def __new__(cls, path: str) -> "StoragePath":
        from infrastructure.storage.factory import StoragePathFactory

        return StoragePathFactory.create(path)
