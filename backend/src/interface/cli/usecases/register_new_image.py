"""新規画像登録CLIモジュール"""

import logging

from pathlib import Path

from application.usecases.register_new_image import RegisterNewImageUsecase
from infrastructure.composition.runtime_factory import RuntimeFactory
from interface.config import app_config


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class RegisterNewImageCLI:
    """Fire CLI class for image registration"""

    def __init__(self) -> None:
        config = app_config
        factory = RuntimeFactory(config)

        self.file_system = factory.create_storage()
        unit_of_work = factory.create_unit_of_work()
        tagger = factory.create_tagger()
        tagger.initialize()
        image_loader = factory.create_image_loader()

        self.usecase = RegisterNewImageUsecase(
            unit_of_work=unit_of_work,
            tagger=tagger,
            image_loader=image_loader,
        )

    def run(self, image_dir: str | Path, n_workers: int = 8, recursive: bool = False) -> None:
        """画像ディレクトリ内のすべての画像を登録する"""
        image_files = self.file_system.list_files(image_dir, recursive=recursive)
        self.usecase.handle(image_files, n_workers=n_workers)


if __name__ == "__main__":
    from fire import Fire

    Fire(RegisterNewImageCLI().run)
