import functools
import inspect

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class ChunkInfo:
    """現在のチャンク処理に関する情報"""

    current_idx: int  # 1から始まる現在のチャンク番号
    total_chunks: int  # 全チャンク数
    offset: int  # 全体の中の開始インデックス
    is_first: bool  # 最初のチャンクかどうか
    is_last: bool  # 最後のチャンクかどうか


def chunk_processor(list_arg_name: str, default_chunk_size: int = 1000):
    def decorator(func: Callable[..., Any]):
        sig = inspect.signature(func)
        has_chunk_info = "chunk_info" in sig.parameters

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            all_items = bound_args.arguments.get(list_arg_name)
            # 引数に chunk_size があれば優先、なければデフォルト
            chunk_size = bound_args.arguments.get("chunk_size", default_chunk_size)

            # chunk_sizeがNone/0、またはリストがサイズ以下の場合は分割せずに実行
            if not chunk_size or not all_items or len(all_items) <= chunk_size:
                return func(*args, **kwargs)

            total = len(all_items)
            total_chunks = (total + chunk_size - 1) // chunk_size
            results = []

            for i in range(0, total, chunk_size):
                current_idx = (i // chunk_size) + 1
                chunk = all_items[i : i + chunk_size]

                # リスト引数をチャンクに差し替え
                bound_args.arguments[list_arg_name] = chunk

                # chunk_infoを欲しがっている場合に注入
                if has_chunk_info:
                    bound_args.arguments["chunk_info"] = ChunkInfo(
                        current_idx=current_idx,
                        total_chunks=total_chunks,
                        offset=i,
                        is_first=(current_idx == 1),
                        is_last=(current_idx == total_chunks),
                    )

                res = func(*bound_args.args, **bound_args.kwargs)
                results.append(res)

            return results

        return wrapper

    return decorator
