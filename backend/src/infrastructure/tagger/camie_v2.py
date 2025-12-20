"""タグ付けモデルによる画像のタグ推論とカテゴリ分類"""

import json

from io import BytesIO
from pathlib import Path
from typing import Final

import numpy as np
import onnxruntime

from PIL import Image
from torchvision import transforms

from application.storage.ports import Storage
from domain.exceptions import TaggingError
from domain.tagger.result import TaggerResult
from domain.tagger.tagger import Tagger
from infrastructure.configs.tagger import CamieV2TaggerModelConfig
from infrastructure.registry.adapter import TaggerAdapterRegistry


@TaggerAdapterRegistry.register("camie_v2")
class CamieTaggerV2(Tagger):
    """タグ付けモデルによる画像のタグ推論とカテゴリ分類を行うクラス

    モデルについて: Camais03/camie-tagger-v2 · Hugging Face](https://huggingface.co/Camais03/camie-tagger-v2)
    """

    def __init__(self, model_dir: str, threshold: float = 0.5) -> None:
        """初期化

        Args:
            threshold (float): タグ推論スコア(logit)の閾値。これ以上のスコアのタグのみを結果に含める。

        参考: logit と確率 (sigmoid) の対応表
            Logit | Prob (sigmoid) | 意味のざっくりした解釈
            ------+----------------+----------------------------------------------
            -5   | 0.0067         | ほぼ絶対に無い（否定強）
            -4   | 0.0179         | かなり無い
            -3   | 0.0474         | ほぼ無い（弱い可能性）
            -2   | 0.1192         | 低め（可能性はあるが弱い）
            -1   | 0.2689         | どちらかというと無い
             0   | 0.5000         | 半々（モデルは判断迷い）
            +1   | 0.7311         | そこそこある
            +2   | 0.8808         | 強めにある
            +3   | 0.9526         | かなり強くある
            +4   | 0.9820         | ほぼ確実にある
            +5   | 0.9933         | ほぼ絶対にある（肯定強）

        """
        self.threshold = threshold
        self.model_file: Final[str] = str(Path(model_dir) / "camie-tagger-v2.onnx")
        self.metadata_file: Final[str] = str(Path(model_dir) / "camie-tagger-v2-metadata.json")

        self.tag_to_idx: dict = {}
        self.tag_to_category: dict = {}
        self.session: onnxruntime.InferenceSession | None = None
        self.input_name: str | None = None

    @classmethod
    def from_config(cls, config: CamieV2TaggerModelConfig) -> "CamieTaggerV2":
        return cls(model_dir=config.model_dir, threshold=config.threshold)

    def _load_tag_mappings(self, storage: Storage) -> tuple[dict, dict]:
        """メタデータJSONからタグ関連情報を読み込む

        Returns:
            tuple[dict, dict]: 2種類のマッピング辞書
                - tag_to_idx: タグ名 -> インデックス
                - tag_to_category: タグ名 -> カテゴリ
        """
        metadata_json = storage.read_text(self.metadata_file)
        metadata = json.loads(metadata_json)

        tag_to_idx = metadata["dataset_info"]["tag_mapping"]["tag_to_idx"]
        tag_to_category = metadata["dataset_info"]["tag_mapping"]["tag_to_category"]
        return tag_to_idx, tag_to_category

    def _start_session(self) -> onnxruntime.InferenceSession:
        """ONNX推論セッションの開始

        Returns:
            onnxruntime.InferenceSession: ONNX推論セッション
        """
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        session = onnxruntime.InferenceSession(self.model_file, providers=providers)
        return session

    def initialize(self, storage: Storage) -> None:
        """モデルとメタデータの読み込み、推論セッションの開始"""
        self.tag_to_idx, self.tag_to_category = self._load_tag_mappings(storage)
        self.session = self._start_session()
        self.input_name = self.session.get_inputs()[0].name

    def _preprocess_image(self, image_binary: bytes) -> np.ndarray:
        """画像を読み込み、モデルに入力できるテンソルへ変換する

        Args:
            image_binary(bytes): 画像バイナリ

        Returns:
            np.ndarray: モデルに入力できるテンソル
        """
        image = Image.open(BytesIO(image_binary)).convert("RGB")

        transform = transforms.Compose(
            [
                transforms.Resize((512, 512)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ],
        )

        tensor = transform(image).unsqueeze(0)
        return tensor.numpy().astype(np.float32)

    def _categorize_tag_scores(self, tag_scores: dict) -> dict[str, list]:
        """推論スコアをカテゴリごとに分類してソートする

        Args:
            tag_scores(dict): タグ名 -> スコア

        Returns:
            dict[str, list]: カテゴリ -> タグ名とスコアのリスト
        """
        categorized_tags: dict[str, list] = {}

        for tag, score in tag_scores.items():
            category = self.tag_to_category.get(tag, "unknown")
            categorized_tags.setdefault(category, []).append((tag, score))

        # カテゴリ内はスコア順に並べ替え
        for items in categorized_tags.values():
            items.sort(key=lambda x: -x[1])

        return categorized_tags

    def tag(self, image_binary: bytes) -> TaggerResult:
        try:
            input_tensor = self._preprocess_image(image_binary)
            if self.session is None:
                msg = "The model session is not initialized. Call 'initialize()' first."
                raise RuntimeError(msg)

            outputs = self.session.run(None, {self.input_name: input_tensor})
            pred = outputs[1][0]  # shape = (70527,)

            tag_scores = {tag: float(pred[idx]) for tag, idx in self.tag_to_idx.items() if pred[idx] >= self.threshold}
            return TaggerResult(tags=self._categorize_tag_scores(tag_scores))
        except Exception as e:
            raise TaggingError(f"Tagging failed: {e}") from e
