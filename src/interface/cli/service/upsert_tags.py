"""既存画像のタグをアップサートするCLIモジュール"""

import logging

from pathlib import Path

import duckdb

from application.inference.camie_v2 import CamieTaggerV2
from application.service.upsert_tags import UpsertTagsService
from config import DATABASE_FILE
from domain.model_name import ModelName
from infrastructure.repositories.images.duck_db import DuckDBImagesRepository
from infrastructure.repositories.model_tag.duck_db import DuckDBModelTagRepository
from infrastructure.storage.local_file_system import LocalFileSystem


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class UpsertTagsCLI:
    """Fire CLI class for upserting tags"""

    def __init__(self) -> None:
        """UpsertTagsCLIを初期化する"""
        conn = duckdb.connect(DATABASE_FILE)

        self.file_system = LocalFileSystem()
        self.service = UpsertTagsService(
            images_repo=DuckDBImagesRepository(conn=conn),
            model_tag_repo=DuckDBModelTagRepository(conn=conn, model_name=ModelName.CAMIE_V2),
            tagger=CamieTaggerV2(threshold=0.0),
        )

    def image(self, image_file: str) -> None:
        """1枚の画像のタグをアップサートする"""
        self.service.upsert_one(image_file)

    def images(self, image_dir: str, n_workers: int = 8, recursive: bool = False) -> None:
        """画像ディレクトリ内のすべての画像のタグを並列でアップサートする"""
        image_files = self.file_system.get_files(image_dir, recursive=recursive)
        self.service.upsert_many(image_files, n_workers=n_workers)


if __name__ == "__main__":
    from fire import Fire

    Fire(UpsertTagsCLI)
