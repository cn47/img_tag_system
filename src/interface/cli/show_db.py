"""データベース内容を表示するCLI"""

from application.config.factory import RuntimeFactory
from interface.cli.utils.pandas_display import set_pandas_display_options
from interface.config import app_config


class ShowDBCLI:
    """Show DB CLI"""

    def __init__(self) -> None:
        """ShowDBCLIを初期化する"""
        self.config = app_config
        self.factory = RuntimeFactory(self.config)

    def images(self, limit: int = 20) -> None:
        """Show images"""
        images_repo = self.factory.create_repository("images")
        images = images_repo.list_all_as_df(limit=limit)
        print(images)

    def model_tag(self, limit: int = 20) -> None:
        """Show model tag"""
        model_tag_repo = self.factory.create_repository("model_tag")
        model_tag = model_tag_repo.list_all_as_df(limit=limit)
        print(model_tag)

    def tables(self) -> None:
        """Show tables"""
        database = self.factory.create_database()
        tables = database.execute("SHOW TABLES").df()
        print(tables)


if __name__ == "__main__":
    import fire

    set_pandas_display_options()

    fire.Fire(ShowDBCLI)
