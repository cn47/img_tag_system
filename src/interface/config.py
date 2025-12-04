from application.config.app_config import AppConfig
from application.config.enums import DataBaseType, StorageType, TaggerType


STORAGE_TYPE = StorageType.LOCAL
DATABASE_TYPE = DataBaseType.DUCKDB
TAGGER_TYPE = TaggerType.CAMIE_V2


app_config = AppConfig.build(
    storage_type=STORAGE_TYPE,
    database_type=DATABASE_TYPE,
    tagger_type=TAGGER_TYPE,
)
