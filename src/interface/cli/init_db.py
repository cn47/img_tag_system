from infrastructure.database.init_db import initialize_database


if __name__ == "__main__":
    import fire

    fire.Fire(initialize_database)
