import time

import pytest

from infrastructure.services.parallel_executor import ExecutionStrategy, execute_parallel


# ========== テスト用の関数 ==========


def simple_task(n: int) -> int:
    """シンプルなタスク: 数値を2倍にして返す"""
    time.sleep(0.01)  # 処理時間をシミュレート
    return n * 2


def process_item(item_id: int, prefix: str = "", suffix: str = "", multiplier: int = 1) -> str:
    """アイテムを処理する関数（argsとkwargsの両方を使用）"""
    time.sleep(0.01)
    value = item_id * multiplier
    return f"{prefix}{value}{suffix}"


def calculate_sum(a: int, b: int, c: int = 0) -> int:
    """3つの数値の合計を計算（argsとkwargsの組み合わせ）"""
    time.sleep(0.01)
    return a + b + c


def task_with_error(n: int) -> int:
    """エラーが発生する可能性があるタスク"""
    time.sleep(0.01)
    if n == 5:
        raise ValueError(f"Error occurred for n={n}")
    return n * 10


def no_args_task() -> str:
    """引数なしのタスク"""
    time.sleep(0.01)
    return "completed"


# ========== テストケース ==========


class TestExecuteParallel:
    """execute_parallel関数のテスト"""

    def test_args_only(self):
        """argsのみを使用する場合のテスト"""
        results = execute_parallel(
            func=simple_task,
            args_list=[(i,) for i in range(5)],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 5
        assert all(not isinstance(r, Exception) for r in results)
        assert results == [0, 2, 4, 6, 8]

    def test_kwargs_only(self):
        """kwargsのみを使用する場合のテスト"""

        def process_file(file_path: str, output_dir: str = "/tmp", encoding: str = "utf-8") -> dict:
            time.sleep(0.01)
            return {
                "file": file_path,
                "output": f"{output_dir}/output.txt",
                "encoding": encoding,
            }

        results = execute_parallel(
            func=process_file,
            kwargs_list=[
                {"file_path": f"/path/to/file{i}.txt", "output_dir": "/tmp/output", "encoding": "utf-8"}
                for i in range(3)
            ],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        assert all(isinstance(r, dict) for r in results)
        assert results[0]["file"] == "/path/to/file0.txt"

    def test_args_and_kwargs(self):
        """argsとkwargsの両方を使用する場合のテスト"""
        results = execute_parallel(
            func=process_item,
            args_list=[(i,) for i in range(4)],
            kwargs_list=[{"prefix": "item_", "suffix": "_processed", "multiplier": 2} for _ in range(4)],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 4
        assert all(not isinstance(r, Exception) for r in results)
        assert results[0] == "item_0_processed"
        assert results[1] == "item_2_processed"
        assert results[2] == "item_4_processed"
        assert results[3] == "item_6_processed"

    def test_different_arguments(self):
        """異なる引数の組み合わせのテスト"""
        results = execute_parallel(
            func=calculate_sum,
            args_list=[(1, 2), (3, 4), (5, 6)],
            kwargs_list=[
                {"c": 10},
                {"c": 20},
                {},
            ],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        assert results[0] == 13  # 1 + 2 + 10
        assert results[1] == 27  # 3 + 4 + 20
        assert results[2] == 11  # 5 + 6 + 0

    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        results = execute_parallel(
            func=task_with_error,
            args_list=[(i,) for i in range(10)],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
            raise_on_error=False,
        )

        assert len(results) == 10
        # タスク5はエラーが発生する
        assert isinstance(results[5], ValueError)
        # その他のタスクは成功
        assert all(not isinstance(r, Exception) for i, r in enumerate(results) if i != 5)

    def test_error_handling_raise(self):
        """エラー時に例外を発生させる場合のテスト"""
        with pytest.raises(ValueError, match="Error occurred for n=5"):
            execute_parallel(
                func=task_with_error,
                args_list=[(5,)],
                n_workers=1,
                strategy=ExecutionStrategy.THREAD,
                show_progress=False,
                raise_on_error=True,
            )

    def test_empty_args_and_kwargs(self):
        """args_listとkwargs_listの両方がNoneの場合のテスト"""
        with pytest.raises(ValueError, match="args_list and kwargs_list must be provided"):
            execute_parallel(
                func=simple_task,
                args_list=None,
                kwargs_list=None,
                n_workers=1,
            )

    def test_different_length_args_and_kwargs(self):
        """args_listとkwargs_listの長さが異なる場合のテスト"""
        with pytest.raises(ValueError, match="must have the same length"):
            execute_parallel(
                func=process_item,
                args_list=[(1,), (2,)],
                kwargs_list=[{"prefix": "item_"}],
                n_workers=1,
            )

    def test_empty_list(self):
        """空のリストの場合のテスト"""
        results = execute_parallel(
            func=simple_task,
            args_list=[],
            n_workers=1,
            show_progress=False,
        )

        assert results == []

    def test_no_args_task(self):
        """引数なしのタスクのテスト"""
        results = execute_parallel(
            func=no_args_task,
            args_list=[() for _ in range(3)],
            n_workers=2,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        assert all(r == "completed" for r in results)

    def test_process_strategy(self):
        """ProcessPoolExecutorを使用する場合のテスト"""
        # ProcessPoolExecutorでは、モジュールレベルの関数を使用する必要がある
        # （ローカル関数はpickleできないため）
        results = execute_parallel(
            func=simple_task,  # モジュールレベルの関数を使用
            args_list=[(i,) for i in range(1, 4)],
            n_workers=2,
            strategy=ExecutionStrategy.PROCESS,
            show_progress=False,
        )

        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        assert all(isinstance(r, int) for r in results)
        assert results == [2, 4, 6]  # simple_taskは n * 2 を返す

    def test_result_order(self):
        """結果の順序が入力の順序と一致することを確認"""
        results = execute_parallel(
            func=simple_task,
            args_list=[(i,) for i in range(10)],
            n_workers=4,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 10
        # 結果は入力の順序と一致する必要がある
        for i, result in enumerate(results):
            assert not isinstance(result, Exception)
            assert result == i * 2

    def test_large_number_of_tasks(self):
        """大量のタスクを処理する場合のテスト"""
        results = execute_parallel(
            func=simple_task,
            args_list=[(i,) for i in range(100)],
            n_workers=8,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 100
        assert all(not isinstance(r, Exception) for r in results)
        assert results == [i * 2 for i in range(100)]

    def test_single_worker(self):
        """単一ワーカーの場合のテスト"""
        results = execute_parallel(
            func=simple_task,
            args_list=[(i,) for i in range(5)],
            n_workers=1,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
        )

        assert len(results) == 5
        assert all(not isinstance(r, Exception) for r in results)

    def test_mixed_success_and_error(self):
        """成功とエラーが混在する場合のテスト"""

        def mixed_task(n: int) -> int:
            time.sleep(0.01)
            if n % 3 == 0:
                raise ValueError(f"Error for n={n}")
            return n * 2

        results = execute_parallel(
            func=mixed_task,
            args_list=[(i,) for i in range(10)],
            n_workers=3,
            strategy=ExecutionStrategy.THREAD,
            show_progress=False,
            raise_on_error=False,
        )

        assert len(results) == 10
        # n=0, 3, 6, 9 はエラー
        error_indices = [0, 3, 6, 9]
        for i, result in enumerate(results):
            if i in error_indices:
                assert isinstance(result, ValueError)
            else:
                assert not isinstance(result, Exception)
                assert result == i * 2
