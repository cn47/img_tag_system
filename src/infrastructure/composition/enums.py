from enum import Enum


class BaseEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class StorageType(BaseEnum):
    LOCAL = "local"


class RepositoryType(BaseEnum):
    IMAGES = "images"
    MODEL_TAG = "model_tag"


class DataBaseType(BaseEnum):
    DUCKDB = "duckdb"


class TaggerType(BaseEnum):
    CAMIE_V2 = "camie_v2"
