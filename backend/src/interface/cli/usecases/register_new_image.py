"""新規画像登録CLIモジュール"""

import logging

from application.usecases.register_new_image import RegisterNewImageUsecase
from infrastructure.composition.runtime_factory import RuntimeFactory
from interface.config import runtime_config


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class RegisterNewImageCLI:
    """Fire CLI class for image registration"""

    def __init__(self) -> None:
        config = runtime_config
        factory = RuntimeFactory(config)

        unit_of_work = factory.create_unit_of_work()
        self.storage = factory.create_storage()
        tagger = factory.create_tagger()
        tagger.initialize(storage=self.storage)

        self.usecase = RegisterNewImageUsecase(
            unit_of_work=unit_of_work,
            tagger=tagger,
            storage=self.storage,
        )

    def run(self, image_dir: str, n_workers: int = 8, recursive: bool = False) -> None:
        """画像ディレクトリ内のすべての画像を登録する"""
        image_files = self.storage.list_files(image_dir, recursive=recursive)
        self.usecase.handle(image_files, n_workers=n_workers)


if __name__ == "__main__":
    from fire import Fire

    Fire(RegisterNewImageCLI().run)
