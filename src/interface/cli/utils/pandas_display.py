"""pandas表示オプション設定ユーティリティ

CLIでのpandas DataFrame表示を制御するためのユーティリティ関数です。
"""

import pandas as pd


def set_pandas_display_options(
    max_rows: int | None = None,
    max_columns: int | None = None,
    max_colwidth: int | None = None,
    width: int | None = 1000,
) -> None:
    """pandasの表示オプションを設定する

    Args:
        max_rows(int | None): 表示する最大行数
        max_columns(int | None): 表示する最大列数
        max_colwidth(int | None): 列の最大幅
        width(int | None): 表示幅
    """
    pd.set_option("display.max_rows", max_rows)
    pd.set_option("display.max_columns", max_columns)
    pd.set_option("display.max_colwidth", max_colwidth)
    pd.set_option("display.width", width)

