"""ドメイン層の例外"""


class DomainError(Exception):
    """ドメインのエラー"""


class UnsupportedFileTypeError(DomainError):
    """サポートされていないファイルタイプのエラー"""


class TaggingError(DomainError):
    """タグ付けのエラー"""


class DuplicateImageError(DomainError):
    """重複画像のエラー"""


class ImageNotFoundError(DomainError):
    """画像が見つからないエラー"""

