from application.system.enums import DataBaseType, StorageType, TaggerType
from infrastructure.composition.runtime_config import RuntimeConfig


STORAGE_TYPE = StorageType.LOCAL
DATABASE_TYPE = DataBaseType.DUCKDB
TAGGER_TYPE = TaggerType.CAMIE_V2


app_config = RuntimeConfig.build(
    storage_type=STORAGE_TYPE,
    database_type=DATABASE_TYPE,
    tagger_type=TAGGER_TYPE,
)
