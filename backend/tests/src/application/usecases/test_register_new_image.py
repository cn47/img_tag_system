from io import BytesIO
from unittest.mock import MagicMock

import pytest

from PIL import Image

from application.service.tagging_result_classifier import TaggedImageEntry, TaggingOutcome
from application.storage.ports import Storage
from application.usecases.register_new_image import RegisterNewImageUsecase
from domain.entities.images import ImageEntry, ImageMetadata
from domain.repositories.unit_of_work import UnitOfWorkProtocol
from domain.tagger.result import TaggerResult
from domain.tagger.tagger import Tagger
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from domain.value_objects.image_size import ImageSize


# ----------------------------
# Mock objects
# ----------------------------


@pytest.fixture
def mock_unit_of_work() -> UnitOfWorkProtocol:
    """UnitOfWorkのモック"""
    uow = MagicMock(spec=UnitOfWorkProtocol)
    uow.__enter__ = MagicMock(return_value=uow)
    uow.__exit__ = MagicMock(return_value=False)

    # リポジトリのモック
    images_repo = MagicMock()
    images_repo.find_by_hashes = MagicMock(return_value=[])
    images_repo.add = MagicMock(return_value=[1])

    model_tag_repo = MagicMock()
    model_tag_repo.add = MagicMock()

    uow.__getitem__ = MagicMock(side_effect=lambda key: {"images": images_repo, "model_tag": model_tag_repo}[key])
    uow.subset = MagicMock(return_value=uow)

    return uow


@pytest.fixture
def mock_storage() -> Storage:
    """Storageのモック"""
    storage = MagicMock(spec=Storage)
    # PILで読み込める形式のダミー画像データを作成
    dummy_image = Image.new("RGB", (1920, 1080), color="red")
    image_bytes = BytesIO()
    dummy_image.save(image_bytes, format="JPEG")
    image_bytes.seek(0)

    storage.read_binary = MagicMock(return_value=image_bytes.getvalue())
    storage.get_size = MagicMock(return_value=1024 * 1024)  # 1MB
    storage.get_file_extension = MagicMock(return_value="jpg")
    return storage


@pytest.fixture
def mock_tagger() -> Tagger:
    """Taggerのモック"""
    tagger = MagicMock(spec=Tagger)
    return tagger


# ----------------------------
# Test data
# ----------------------------


@pytest.fixture
def image_files_one() -> list[str]:
    """1つの画像ファイルパスのリスト"""
    return ["tests/data/images/test.jpg"]


@pytest.fixture
def image_files_many() -> list[str]:
    """複数の画像ファイルパスのリスト"""
    return [
        "tests/data/images/test.jpg",
        "tests/data/images/test.png",
        "tests/data/images/test.webp",
    ]


@pytest.fixture
def tagger_result() -> TaggerResult:
    """TaggerResultのモック"""
    return TaggerResult(
        {
            "artist": [("artist_name", 4.21)],
            "rating": [("rating_questionable", 2.21)],
            "general": [("cardigan", 2.32), ("1girl", 0.79)],
            "character": [("vignette_tsukinose_april", 4.76)],
            "copyright": [("gabriel_dropout", 3.48)],
        },
    )


@pytest.fixture
def tagger_results() -> list[TaggerResult]:
    """TaggerResultのリストのモック"""
    return [
        TaggerResult(
            {
                "artist": [("artist_name", 4.21)],
                "rating": [("rating_questionable", 2.21)],
                "general": [("cardigan", 2.32), ("1girl", 0.79)],
                "character": [("vignette_tsukinose_april", 4.76)],
                "copyright": [("gabriel_dropout", 3.48)],
            },
        ),
        TaggerResult(
            {
                "artist": [("artist_name", 4.21)],
                "rating": [("rating_safe", 3.21)],
                "general": [("cardigan", 2.32), ("1girl", 0.79)],
                "character": [("kokkoro_(princess_connect!)", 5.76)],
                "copyright": [("princess_connect", 3.50)],
            },
        ),
        TaggerResult(
            {
                "artist": [("artist_name", 4.21)],
                "rating": [("rating_explicit", 4.21)],
                "general": [("maid", 2.32), ("1girl", 0.79)],
                "character": [("shirakami_fubuki_(blue_archive)", 5.76)],
                "copyright": [("blue_archive", 3.50)],
            },
        ),
    ]


# ----------------------------
# Helper functions
# ----------------------------


def make_tagged_image_entry() -> TaggedImageEntry:
    return TaggedImageEntry(image_entry=MagicMock(), tagger_result=MagicMock())


def create_image_entry(file_path: str, hash_value: str = "a" * 64) -> ImageEntry:
    """ImageEntryを作成するヘルパー関数"""
    file_location = FileLocation(file_path)
    image_hash = ImageHash(hash_value)
    image_size = ImageSize(width=1920, height=1080)

    metadata = ImageMetadata(
        file_location=file_location,
        hash=image_hash,
        size=image_size,
        file_type="jpg",
        file_size=1024 * 1024,
    )

    return ImageEntry.from_metadata(metadata)


def assert_metadata_extraction_call_count(storage: Storage, expected_count: int) -> None:
    """メタデータ抽出が呼ばれたかを検証するヘルパー関数"""
    if expected_count == 0:
        storage.read_binary.assert_not_called()
        storage.get_size.assert_not_called()
        storage.get_file_extension.assert_not_called()
    else:
        assert storage.read_binary.call_count == expected_count
        assert storage.get_size.call_count == expected_count
        assert storage.get_file_extension.call_count == expected_count


def assert_add_call_count(repository: MagicMock, expected_count: int) -> None:
    """addの呼び出し回数と引数の数を検証するヘルパー関数"""
    if expected_count == 0:
        repository.add.assert_not_called()
    else:
        repository.add.assert_called_once()
        add_args = repository.add.call_args[0][0]
        assert len(add_args) == expected_count


class TestRegisterNewImageUsecaseValid:
    """正常系のテスト

    テストケース:
        - 1件の画像を登録する: test_handle_one_image
        - 複数件の画像を登録する: test_handle_many_images
        - 空の画像ファイルリストが入力される: test_empty_image_files_input
        - タグ付け結果に異常ケースが含まれていた場合の処理スキップ: test_tagging_result_with_abnormal_cases
            - タグ付け結果が空（すべてのタグ付け結果が閾値を下回った場合）
            - タグ付けが失敗した場合
    """

    def test_handle_one_image(
        self,
        image_files_one: list[str],
        tagger_result: TaggerResult,
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_storage: Storage,
        mock_tagger: Tagger,
    ) -> None:
        """1件の画像を登録する"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            storage=mock_storage,
        )

        # タガーのモック設定
        mock_tagger.tag = MagicMock(return_value=tagger_result)

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出が呼ばれたか
        assert_metadata_extraction_call_count(mock_storage, 1)

        # 2. 重複チェックが呼ばれたか
        assert images_repo.find_by_hashes.called

        # 3. タグ付けが呼ばれたか
        assert mock_tagger.tag.called

        # 4.データベースへの永続化が呼ばれたか
        assert_add_call_count(images_repo, 1)
        assert_add_call_count(model_tag_repo, 1)

        # 5. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_called_once()

    def test_handle_many_images(
        self,
        image_files_many: list[str],
        tagger_results: list[TaggerResult],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_storage: Storage,
        mock_tagger: Tagger,
    ) -> None:
        """複数件の画像を登録する"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            storage=mock_storage,
        )

        # タガーのモック設定（複数の結果を返す）
        mock_tagger.tag = MagicMock(side_effect=tagger_results)

        # リポジトリのモック設定（複数のIDを返す）
        images_repo = mock_unit_of_work["images"]
        images_repo.add.return_value = [1, 2, 3]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_many, n_workers=2)

        # 検証
        # 1. メタデータ抽出が呼ばれたか（3回）
        assert_metadata_extraction_call_count(mock_storage, 3)

        # 2. タグ付けが呼ばれたか（3回）
        assert mock_tagger.tag.call_count == 3

        # 3. データベースへの永続化が呼ばれたか
        assert_add_call_count(images_repo, 3)
        assert_add_call_count(model_tag_repo, 3)

        # 4. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_called_once()

    def test_empty_image_files_input(
        self,
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_storage: Storage,
        mock_tagger: Tagger,
    ) -> None:
        """空の画像ファイルリストが入力される"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            storage=mock_storage,
        )

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle([], n_workers=1)

        # 検証
        # 何も呼ばれない
        assert_metadata_extraction_call_count(mock_storage, 0)

        assert not mock_tagger.tag.called

        assert_add_call_count(images_repo, 0)
        assert_add_call_count(model_tag_repo, 0)

        assert not mock_unit_of_work.__exit__.called

    @pytest.mark.parametrize(
        "outcome, expected_add_count",
        [
            (TaggingOutcome(success=[], failure=[], empty=[]), 0),
            (TaggingOutcome(success=[], failure=[MagicMock()], empty=[]), 0),
            (TaggingOutcome(success=[], failure=[], empty=[MagicMock()]), 0),
            (TaggingOutcome(success=[make_tagged_image_entry()], failure=[], empty=[MagicMock()]), 1),
            # NOTE: 重複画像除外処理を入れてるからこれはテストできない(add数が1になってしまう)
            # (TaggingOutcome(success=[make_tagged_image_entry()] * 3, failure=[MagicMock()], empty=[MagicMock()]), 3),
        ],
        ids=[
            "no_outcome",
            "failure_only",
            "empty_only",
            "success_and_empty",
            # "success_many_and_failure_and_empty",
        ],
    )
    def test_tagging_result_with_abnormal_cases(
        self,
        monkeypatch: pytest.MonkeyPatch,
        outcome: TaggingOutcome,
        expected_add_count: int,
        image_files_one: list[str],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_storage: Storage,
        mock_tagger: Tagger,
    ) -> None:
        """タグ付け結果に異常ケースが含まれていた場合の処理スキップ"""
        # monkeypatchをあててclassifyメソッドを差し替え
        monkeypatch.setattr(
            "application.service.tagging_result_classifier.TaggingResultClassifier.classify",
            lambda *_: outcome,
        )

        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            storage=mock_storage,
        )

        # タガーのモック設定
        mock_tagger.tag = MagicMock()

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行: monkeypatchの差し替えをしてるので画像ファイル数は適当に1つにしておく
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出が呼ばれたか
        assert_metadata_extraction_call_count(mock_storage, 1)

        # 2. データベースへの永続化が呼ばれたか
        assert_add_call_count(images_repo, expected_add_count)
        assert_add_call_count(model_tag_repo, expected_add_count)

        # 4. コミットが呼ばれたか
        if expected_add_count > 0:
            mock_unit_of_work.__exit__.assert_called_once()
        else:
            mock_unit_of_work.__exit__.assert_not_called()


class TestRegisterNewImageUsecaseInvalid:
    """異常系のテスト

    テストケース:
        - サポートされていないファイル形式の画像が入力される: test_unsupported_file_type_input
    """

    def test_unsupported_file_type_input(
        self,
        image_files_one: list[str],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_storage: Storage,
        mock_tagger: Tagger,
    ) -> None:
        """サポートされていないファイル形式の画像が入力される"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            storage=mock_storage,
        )

        # サポートされていないファイル形式のエラーを発生させる
        # ImageMetadataExtractorはUnidentifiedImageErrorをキャッチしてNoneを返すので、
        # extract_from_filesは空のリストを返す
        # read_binaryで読み込んだ後、PIL.Image.openでUnidentifiedImageErrorが発生するようにする
        mock_storage.read_binary = MagicMock(return_value=b"invalid_image_data")
        mock_storage.get_size = MagicMock(return_value=1024)
        mock_storage.get_file_extension = MagicMock(return_value="jpg")

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出は試みられた
        mock_storage.read_binary.assert_called_once()
        mock_storage.get_size.assert_not_called()
        mock_storage.get_file_extension.assert_not_called()

        # 2. データベースへの永続化が呼ばれたか
        # 画像は挿入されない（メタデータ抽出失敗によりフィルタリングされる）
        # タグ付けも呼ばれない（image_entriesが空なので）
        assert_add_call_count(images_repo, 0)
        assert_add_call_count(model_tag_repo, 0)

        # 3. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_not_called()
