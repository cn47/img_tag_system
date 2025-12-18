from typing import TYPE_CHECKING
from urllib.parse import urlparse

from infrastructure.storage.local import LocalStoragePath


if TYPE_CHECKING:
    from infrastructure.storage.base import StoragePath


class StoragePathFactory:
    """ストレージパスファクトリー

    直接インスタンス化することで、URIプレフィックスに応じて
    適切な具象クラス（LocalStoragePath、S3StoragePathなど）を返す

    Examples:
        >>> path = StoragePath("/path/to/image.jpg")
        LocalStoragePath('/path/to/image.jpg')
    """

    @staticmethod
    def create(path: str) -> "StoragePath":
        """パスから適切なStoragePathを作成

        URIプレフィックスに応じて適切な具象クラスを返す

        Args:
            path(str): パス文字列

        Returns:
            StoragePathProtocol: StoragePathのインスタンス

        Examples:
            >>> StoragePath.create("/path/to/image.jpg")
            LocalStoragePath('/path/to/image.jpg')
        """
        path_str = str(path)

        # URLスキームで判定
        scheme = urlparse(path_str).scheme or "file"
        match scheme:
            case "file":
                return LocalStoragePath(path_str.removeprefix("file://"))
            case "s3":
                raise NotImplementedError("S3 Storage is not yet supported")
            case "gs":
                raise NotImplementedError("GCS Storage is not yet supported")
            case _:
                # NOTE: Windowsのパスは一旦想定外とする
                raise ValueError(f"Invalid scheme: {scheme}")

    # @staticmethod
    # def _create_s3_path(uri: str) -> S3StoragePath:
    #     """s3://bucket/key 形式からS3StoragePathを作成"""
    #     return S3StoragePath.from_string(uri)

    # @staticmethod
    # def _create_gcs_path(uri: str) -> GCSStoragePath:
    #     """gs://bucket/blob 形式からGCSStoragePathを作成"""
    #     return GCSStoragePath.from_string(uri)
