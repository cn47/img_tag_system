from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from inference.tag_types import TaggerResult
from inference.tagging import CamieTaggerV2


def _make_dummy_session(pred_array: np.ndarray):
    """簡易セッションモックを作成するヘルパー

    Args:
        pred_array (np.ndarray): 1次元の予測スコア配列。len = クラス数

    Returns:
        SimpleNamespace: run メソッドを持つモックオブジェクト
    """

    class DummySession:
        def run(self, _, feed):
            # tagging.tag_image_file は outputs[1][0] を参照するので形を合わせる
            return [None, np.array([pred_array])]

    return DummySession()


def test_tag_image_file_without_session_raises():
    """session が未初期化のとき、RuntimeError が発生することを検証する

    期待値:
        CamieTaggerV2.tag_image_file 呼び出しで RuntimeError が発生する
    """
    tagger = CamieTaggerV2(model_dir=Path("dummy"), threshold=0.5)
    # session を初期化せずに呼ぶと例外
    with pytest.raises(RuntimeError):
        tagger.tag_image_file("ignored.jpg")


def test_tag_image_file_filters_and_groups(monkeypatch):
    """出力スコアが閾値でフィルタされ、カテゴリ別にソートされることを検証する

    セットアップ:
        - 3 クラスのマッピングを用意（tag_a, tag_b, tag_c）
        - tag_to_idx と tag_to_category を直接注入
        - session.run はカスタム予測配列を返すようモック
        - _preprocess_image をモックしてファイルアクセスを避ける

    期待値:
        - threshold=0.5 によりスコア >= 0.5 のタグのみ結果に含まれる
        - 同カテゴリ内はスコア降順で並ぶため top は最大スコアのタグになる
    """
    tagger = CamieTaggerV2(model_dir=Path("dummy"), threshold=0.5)

    # タグとカテゴリの簡易マッピングを注入
    tagger.tag_to_idx = {"tag_a": 0, "tag_b": 1, "tag_c": 2}
    tagger.tag_to_category = {"tag_a": "general", "tag_b": "artist", "tag_c": "general"}

    # 予測スコア配列: tag_a=0.7, tag_b=0.4, tag_c=0.9
    pred = np.array([0.7, 0.4, 0.9], dtype=np.float32)
    tagger.session = _make_dummy_session(pred)
    tagger.input_name = "input0"

    # _preprocess_image をモックして実際のファイル読み込みを行わない
    monkeypatch.setattr(tagger, "_preprocess_image", lambda image_file: np.zeros((1, 3, 512, 512), dtype=np.float32))

    result = tagger.tag_image_file("ignored.jpg")

    # 型と戻り値の基本検証
    assert isinstance(result, TaggerResult)
    # categories は metadata 由来なので、_original_tags のキーが反映される
    cats = result.categories
    assert "general" in cats and "artist" in cats

    # to_dict_list に含まれる要素は threshold を満たす 2 つのタグのみ
    dict_list = result.to_dict_list()
    names = {d["name"] for d in dict_list}
    assert names == {"tag_a", "tag_c"}

    # general カテゴリのトップ（.name）は tag_c (score 0.9) になる
    assert result.general.name == "tag_c"
    assert result.general.score == pytest.approx(0.9)

    # artist は 0.4 < 0.5 なので空 (None)
    assert result.artist.name is None
    assert result.artist.score is None
