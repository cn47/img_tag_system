from dataclasses import dataclass


@dataclass(frozen=True)
class ImageSize:
    """画像サイズの値オブジェクト

    画像の幅と高さを表現する値オブジェクトです。
    イミュータブルで、バリデーション機能を提供します。

    Attributes:
        width(int): 画像の幅（ピクセル）
        height(int): 画像の高さ（ピクセル）

    Raises:
        ValueError: 幅または高さが0以下の場合

    Example:
        >>> size = ImageSize(width=1920, height=1080)
        >>> size.width
        1920
        >>> size.height
        1080
        >>> size.aspect_ratio
        1.7777777777777777
    """

    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError(f"Width must be positive, got {self.width}")
        if self.height <= 0:
            raise ValueError(f"Height must be positive, got {self.height}")

    @property
    def aspect_ratio(self) -> float:
        """アスペクト比を計算

        Returns:
            float: 幅 ÷ 高さの比率
        """
        return self.width / self.height

    @property
    def total_pixels(self) -> int:
        """総ピクセル数を計算

        Returns:
            int: 幅 × 高さ
        """
        return self.width * self.height
