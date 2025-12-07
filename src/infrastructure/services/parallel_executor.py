from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from enum import Enum
from logging import getLogger
from typing import Any, TypeVar

from tqdm import tqdm


logger = getLogger(__name__)
T = TypeVar("T")


class ExecutionStrategy(str, Enum):
    """並列実行ストラテジー"""

    THREAD = "thread"
    PROCESS = "process"


def execute_parallel[T](
    func: Callable[..., T],
    args_list: list[tuple[Any, ...]] | None = None,
    kwargs_list: list[dict[str, Any]] | None = None,
    *,
    n_workers: int,
    strategy: ExecutionStrategy = ExecutionStrategy.THREAD,
    show_progress: bool = True,
    description: str = "Processing",
    raise_on_error: bool = False,
) -> list[T | Exception]:
    """関数の引数リストを並列実行

    Args:
        func: 実行する関数
        args_list: 各タスクに渡す位置引数のリスト。省略可能
        kwargs_list: 各タスクに渡すキーワード引数のリスト。省略可能
        n_workers: 並列実行の最大並列数
        strategy: 並列実行ストラテジー
        show_progress: 進捗バーを表示するかどうか
        description: 進捗バーの説明
        raise_on_error: エラーが発生した場合に例外を発生させるかどうか

    Returns:
        list[T | Exception]: 実行結果のリスト
        入力された引数リストの順番に実行結果が返ってくる

    Note:
        args_list と kwargs_list の少なくとも一方は指定する必要がある
    """
    # バリデーション
    if args_list is None and kwargs_list is None:
        raise ValueError("args_list and kwargs_list must be provided")

    # デフォルト値の設定
    if args_list is None:
        args_list = []
    if kwargs_list is None:
        kwargs_list = []

    # 長さの検証と調整
    if args_list and kwargs_list:
        if len(args_list) != len(kwargs_list):
            raise ValueError(
                f"args_list and kwargs_list must have the same length. Got {len(args_list)} and {len(kwargs_list)}"
            )
        num_tasks = len(args_list)
    elif args_list:
        num_tasks = len(args_list)
        kwargs_list = [{}] * num_tasks
    else:  # kwargs_list only
        num_tasks = len(kwargs_list)
        args_list = [()] * num_tasks

    executor_class = ThreadPoolExecutor if strategy == ExecutionStrategy.THREAD else ProcessPoolExecutor

    results: list[T | Exception] = [None] * num_tasks  # type: ignore[list-item]

    with executor_class(max_workers=n_workers) as ex:
        futures = {
            ex.submit(func, *args, **kwargs): idx
            for idx, (args, kwargs) in enumerate(zip(args_list, kwargs_list, strict=True))
        }

        iterator = as_completed(futures)
        if show_progress:
            iterator = tqdm(iterator, total=num_tasks, desc=description)

        for future in iterator:
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                if raise_on_error:
                    raise
                results[idx] = e

    return results
