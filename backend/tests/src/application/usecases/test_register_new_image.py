from pathlib import Path
from unittest.mock import MagicMock

import pytest

from application.image_loader import ImageLoader
from application.usecases.register_new_image import RegisterNewImageUsecase
from domain.entities.images import ImageEntry, ImageMetadata
from domain.exceptions import TaggingError, UnsupportedFileTypeError
from domain.repositories.unit_of_work import UnitOfWorkProtocol
from domain.services.tagging_result_classifier import TaggedImageEntry, TaggingOutcome
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
    images_repo.insert = MagicMock(return_value=[1])

    model_tag_repo = MagicMock()
    model_tag_repo.insert = MagicMock()

    uow.__getitem__ = MagicMock(side_effect=lambda key: {"images": images_repo, "model_tag": model_tag_repo}[key])
    uow.subset = MagicMock(return_value=uow)

    return uow


@pytest.fixture
def mock_image_loader() -> ImageLoader:
    """ImageLoaderのモック"""
    loader = MagicMock(spec=ImageLoader)
    loader.load_binary = MagicMock(return_value=b"fake_image_binary_data")
    loader.extract_size = MagicMock(return_value=ImageSize(width=1920, height=1080))
    loader.get_file_size = MagicMock(return_value=1024 * 1024)  # 1MB
    return loader


@pytest.fixture
def mock_tagger() -> Tagger:
    """Taggerのモック"""
    tagger = MagicMock(spec=Tagger)
    return tagger


# ----------------------------
# Test data
# ----------------------------


@pytest.fixture
def image_files_one():
    return [Path("tests/data/images/test.jpg")]


@pytest.fixture
def image_files_many():
    return [
        Path("tests/data/images/test.jpg"),
        Path("tests/data/images/test.png"),
        Path("tests/data/images/test.webp"),
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


def create_image_entry(file_path: Path, hash_value: str = "a" * 64) -> ImageEntry:
    """ImageEntryを作成するヘルパー関数"""
    file_location = FileLocation(str(file_path))
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


def assert_metadata_extraction_call_count(image_loader: ImageLoader, expected_count: int):
    """メタデータ抽出が呼ばれたかを検証するヘルパー関数"""
    if expected_count == 0:
        image_loader.load_binary.assert_not_called()
        image_loader.extract_size.assert_not_called()
        image_loader.get_file_size.assert_not_called()
    else:
        assert image_loader.load_binary.call_count == expected_count
        assert image_loader.extract_size.call_count == expected_count
        assert image_loader.get_file_size.call_count == expected_count


def assert_insert_call_count(repository: MagicMock, expected_count: int):
    """insertの呼び出し回数と引数の数を検証するヘルパー関数"""
    if expected_count == 0:
        repository.insert.assert_not_called()
    else:
        repository.insert.assert_called_once()
        insert_args = repository.insert.call_args[0][0]
        assert len(insert_args) == expected_count


class TestRegisterNewImageUsecaseValid:
    """正常系のテスト

    テストケース:
        - 1件の画像を登録する
        - 複数件の画像を登録する
        - 空の画像ファイルリストが入力される
        - タグ付け結果に異常ケースが含まれていた場合の処理スキップ
            - タグ付け結果が空（すべてのタグが閾値を下回った場合）
            - タグ付けが失敗した場合
    """

    def test_handle_one_image(
        self,
        image_files_one: list[Path],
        tagger_result: TaggerResult,
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_image_loader: ImageLoader,
        mock_tagger: Tagger,
    ):
        """1件の画像を登録する"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            image_loader=mock_image_loader,
        )

        # タガーのモック設定
        mock_tagger.tag_image_file = MagicMock(return_value=tagger_result)

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出が呼ばれたか
        assert_metadata_extraction_call_count(mock_image_loader, 1)

        # 2. 重複チェックが呼ばれたか
        assert images_repo.find_by_hashes.called

        # 3. タグ付けが呼ばれたか
        assert mock_tagger.tag_image_file.called

        # 4.データベースへの永続化が呼ばれたか
        assert_insert_call_count(images_repo, 1)
        assert_insert_call_count(model_tag_repo, 1)

        # 5. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_called_once()

    def test_handle_many_images(
        self,
        image_files_many: list[Path],
        tagger_results: list[TaggerResult],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_image_loader: ImageLoader,
        mock_tagger: Tagger,
    ):
        """複数件の画像を登録する"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            image_loader=mock_image_loader,
        )

        # タガーのモック設定（複数の結果を返す）
        mock_tagger.tag_image_file = MagicMock(side_effect=tagger_results)

        # リポジトリのモック設定（複数のIDを返す）
        images_repo = mock_unit_of_work["images"]
        images_repo.insert.return_value = [1, 2, 3]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_many, n_workers=2)

        # 検証
        # 1. メタデータ抽出が呼ばれたか（3回）
        assert_metadata_extraction_call_count(mock_image_loader, 3)

        # 2. タグ付けが呼ばれたか（3回）
        assert mock_tagger.tag_image_file.call_count == 3

        # 3. データベースへの永続化が呼ばれたか
        assert_insert_call_count(images_repo, 3)
        assert_insert_call_count(model_tag_repo, 3)

        # 4. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_called_once()

    def test_empty_image_files_input(
        self,
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_image_loader: ImageLoader,
        mock_tagger: Tagger,
    ):
        """空の画像ファイルリストが入力される"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            image_loader=mock_image_loader,
        )

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle([], n_workers=1)

        # 検証
        # 何も呼ばれない
        assert_metadata_extraction_call_count(mock_image_loader, 0)

        assert not mock_tagger.tag_image_file.called

        assert_insert_call_count(images_repo, 0)
        assert_insert_call_count(model_tag_repo, 0)

        assert not mock_unit_of_work.__exit__.called

    @pytest.mark.parametrize(
        "outcome, expected_insert_count",
        [
            (TaggingOutcome(success=[], failure=[], empty=[]), 0),
            (TaggingOutcome(success=[], failure=[MagicMock()], empty=[]), 0),
            (TaggingOutcome(success=[], failure=[], empty=[MagicMock()]), 0),
            (TaggingOutcome(success=[make_tagged_image_entry()], failure=[], empty=[MagicMock()]), 1),
            # NOTE: 重複画像除外処理を入れてるからこれはテストできない(insert数が1になってしまう)
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
        expected_insert_count: int,
        image_files_one: list[Path],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_image_loader: ImageLoader,
        mock_tagger: Tagger,
    ):
        """タグ付け結果に異常ケースが含まれていた場合の処理スキップ"""
        # monkeypatchをあててclassifyメソッドを差し替え
        monkeypatch.setattr(
            "domain.services.tagging_result_classifier.TaggingResultClassifier.classify",
            lambda *_: outcome,
        )

        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            image_loader=mock_image_loader,
        )

        # タガーのモック設定
        mock_tagger.tag_image_file = MagicMock()

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行: monkeypatchの差し替えをしてるので画像ファイル数は適当に1つにしておく
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出が呼ばれたか
        assert_metadata_extraction_call_count(mock_image_loader, 1)

        # 2. データベースへの永続化が呼ばれたか
        assert_insert_call_count(images_repo, expected_insert_count)
        assert_insert_call_count(model_tag_repo, expected_insert_count)

        # 4. コミットが呼ばれたか
        if expected_insert_count > 0:
            mock_unit_of_work.__exit__.assert_called_once()
        else:
            mock_unit_of_work.__exit__.assert_not_called()


class TestRegisterNewImageUsecaseInvalid:
    """異常系のテスト

    テストケース:
        - サポートされていないファイル形式の画像が入力される
        - 画像ファイルが存在しない
    """

    def test_unsupported_file_type_input(
        self,
        image_files_one: list[Path],
        mock_unit_of_work: UnitOfWorkProtocol,
        mock_image_loader: ImageLoader,
        mock_tagger: Tagger,
    ):
        """サポートされていないファイル形式の画像が入力される"""
        # セットアップ
        usecase = RegisterNewImageUsecase(
            unit_of_work=mock_unit_of_work,
            tagger=mock_tagger,
            image_loader=mock_image_loader,
        )

        # サポートされていないファイル形式のエラーを発生させる
        # ImageMetadataExtractorは例外をキャッチしてNoneを返すので、
        # extract_from_filesは空のリストを返す
        mock_image_loader.load_binary = MagicMock(side_effect=UnsupportedFileTypeError("Unsupported file type"))

        # リポジトリのモック設定
        images_repo = mock_unit_of_work["images"]
        model_tag_repo = mock_unit_of_work["model_tag"]

        # 実行
        usecase.handle(image_files_one, n_workers=1)

        # 検証
        # 1. メタデータ抽出は試みられた
        mock_image_loader.load_binary.assert_called_once()
        mock_image_loader.extract_size.assert_not_called()
        mock_image_loader.get_file_size.assert_not_called()

        # 2. データベースへの永続化が呼ばれたか
        # 画像は挿入されない（メタデータ抽出失敗によりフィルタリングされる）
        # タグ付けも呼ばれない（image_entriesが空なので）
        assert_insert_call_count(images_repo, 0)
        assert_insert_call_count(model_tag_repo, 0)

        # 3. コミットが呼ばれたか
        mock_unit_of_work.__exit__.assert_not_called()
