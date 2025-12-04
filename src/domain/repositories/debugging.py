from typing import TYPE_CHECKING, Protocol


if TYPE_CHECKING:
    import pandas as pd


class DebuggableRepository(Protocol):
    """開発・検証用に利用するRepositoryユーティリティ"""

    def count(self) -> int:
        """総件数

        Args:
            None

        Returns:
            int: 総件数
        """
        ...

    def list_all_as_df(self, limit: int = 20) -> "pd.DataFrame":
        """開発・検証用: データベースの中身を取得

        Args:
            limit(int): 取得件数

        Returns:
            pd.DataFrame: データベースの中身

        Note:
            開発・デバッグ用のメソッドであるため、本番環境では使用しないこと。
        """
        ...
