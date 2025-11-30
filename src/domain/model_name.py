from enum import Enum


class ModelName(Enum):
    CAMIE_V2 = "camie_v2"

    def __str__(self) -> str:
        return self.value
