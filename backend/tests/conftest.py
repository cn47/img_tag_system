import multiprocessing as mp

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_multiprocessing_start_method():
    mp.set_start_method("spawn", force=True)
