from dataclasses import dataclass, field
from pathlib import Path

from common.path_utils import get_project_root
from infrastructure.registry.config import TaggerConfigRegistry


@dataclass(frozen=True)
class TaggerModelConfig:
    """タグ付けモデルの設定の基底インターフェースクラス"""

    @property
    def adapter_key(self) -> str:
        raise NotImplementedError


@TaggerConfigRegistry.register("camie_v2")
@dataclass(frozen=True)
class CamieV2TaggerModelConfig(TaggerModelConfig):
    """Camie V2モデルの設定"""

    model_dir: Path = field(default_factory=lambda: get_project_root() / "data" / "model" / "camie-tagger-v2")
    threshold: float = 0.0

    @property
    def tag_table_name(self) -> str:
        return "tags_camie_v2"

    @property
    def adapter_key(self) -> str:
        return "camie_v2"

