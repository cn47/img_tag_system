from dataclasses import dataclass


@dataclass(frozen=True)
class FileLocation:
    """ファイル位置の値オブジェクト

    ファイルパスやファイル位置を表現する値オブジェクトです。
    イミュータブルで、バリデーション機能を提供します。

    Attributes:
        value(str): ファイルパス

    Raises:
        ValueError: ファイル位置が空、または空白のみの場合

    Example:
        >>> location = FileLocation("/path/to/image.jpg")
        >>> str(location)
        '/path/to/image.jpg'
        >>> location == FileLocation("/path/to/image.jpg")
        True
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("File location cannot be empty")
        if not self.value.strip():
            raise ValueError("File location cannot be whitespace only")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"FileLocation('{self.value}')"
