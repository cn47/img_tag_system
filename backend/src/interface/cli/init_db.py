from infrastructure.composition.runtime_factory import RuntimeFactory
from infrastructure.database.init_db import initialize_database
from interface.config import runtime_config


class InitDBCLI:
    """Init DB CLI"""

    def __init__(self) -> None:
        self.config = runtime_config
        factory = RuntimeFactory(self.config)
        self.storage = factory.create_storage()

    def run(self, overwrite: bool = False) -> None:
        initialize_database(
            storage=self.storage,
            db_file=self.config.database.database_file,
            schema_file=f"{self.storage.root_dir}/backend/src/infrastructure/database/schema.sql",
            overwrite=overwrite,
        )


if __name__ == "__main__":
    import fire

    fire.Fire(InitDBCLI().run)
