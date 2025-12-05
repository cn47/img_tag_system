"""新規画像登録CLIモジュール"""

import logging
from pathlib import Path

from application.config.factory import RuntimeFactory
from application.service.new_image_register import NewImageRegisterService
from interface.config import app_config


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class NewImageRegisterCLI:
    """Fire CLI class for image registration"""

    def __init__(self) -> None:
        config = app_config
        factory = RuntimeFactory(config)

        self.file_system = factory.create_storage()
        images_repo = factory.create_repository("images")
        model_tag_repo = factory.create_repository("model_tag")
        tagger = factory.create_tagger()
        tagger.initialize()

        self.service = NewImageRegisterService(
            images_repo=images_repo,
            model_tag_repo=model_tag_repo,
            tagger=tagger,
        )

    def run(self, image_dir: str | Path, n_workers: int = 8, recursive: bool = False) -> None:
        """画像ディレクトリ内のすべての画像を登録する"""
        image_files = self.file_system.list_files(image_dir, recursive=recursive)
        self.service.handle(image_files, n_workers=n_workers)


if __name__ == "__main__":
    from fire import Fire

    Fire(NewImageRegisterCLI().run)
