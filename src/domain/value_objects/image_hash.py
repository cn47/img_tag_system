from dataclasses import dataclass


@dataclass(frozen=True)
class ImageHash:
    """画像ハッシュの値オブジェクト（SHA256）"""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Hash cannot be empty")
        if len(self.value) != 64:  # SHA256のhexdigest長
            raise ValueError(f"Invalid hash format: expected 64 characters, got {len(self.value)}")
        # 16進数の文字列かチェック
        try:
            int(self.value, 16)
        except ValueError as e:
            raise ValueError(f"Invalid hash format: not a valid hexadecimal string: {self.value[:20]}...") from e

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ImageHash('{self.value}')"
