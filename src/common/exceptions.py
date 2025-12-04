class ApplicationError(Exception):
    """アプリケーションのエラー"""


class UnsupportedFileTypeError(ApplicationError):
    """サポートされていないファイルタイプのエラー"""


class TaggingError(ApplicationError):
    """タグ付けのエラー"""


class InfrastructureError(Exception):
    """インフラストラクチャーのエラー"""


class DuplicateImageError(InfrastructureError):
    """重複画像のエラー"""


class ImageNotFoundError(InfrastructureError):
    """画像が見つからないエラー"""

