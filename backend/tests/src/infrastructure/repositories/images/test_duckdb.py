import pytest

from domain.entities.images import ImageEntry, ImageMetadata
from domain.exceptions import DuplicateImageError
from domain.value_objects.file_location import FileLocation
from domain.value_objects.image_hash import ImageHash
from domain.value_objects.image_size import ImageSize
from infrastructure.repositories.images.duckdb import DuckDBImagesRepository


# ----------------------------
# Fixtures
# ----------------------------


@pytest.fixture
def db_schema() -> str:
    """データベーススキーマSQL"""
    return """
    CREATE SEQUENCE IF NOT EXISTS image_id_seq START 1 INCREMENT 1;

    CREATE TABLE IF NOT EXISTS images (
        image_id       INTEGER PRIMARY KEY DEFAULT NEXTVAL('image_id_seq'),
        file_location  TEXT NOT NULL,
        width          INTEGER,
        height         INTEGER,
        file_type      TEXT,
        hash           TEXT NOT NULL UNIQUE,
        file_size      INTEGER,
        added_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """


@pytest.fixture
def repository(db_schema: str) -> DuckDBImagesRepository:
    repo = DuckDBImagesRepository(database_file=":memory:", table_name="images")
    repo.conn.execute(db_schema)
    return repo


# ----------------------------
# Test data
# ----------------------------


def create_image_entry(
    file_path: str,
    hash_value: str = "a" * 64,
    width: int = 1920,
    height: int = 1080,
    file_type: str = "jpg",
    file_size: int = 1024 * 1024,
) -> ImageEntry:
    """ImageEntryを作成するヘルパー関数"""
    file_location = FileLocation(file_path)
    image_hash = ImageHash(hash_value)
    image_size = ImageSize(width=width, height=height)

    metadata = ImageMetadata(
        file_location=file_location,
        hash=image_hash,
        size=image_size,
        file_type=file_type,
        file_size=file_size,
    )

    return ImageEntry.from_metadata(metadata)


@pytest.fixture
def image_entry_one() -> ImageEntry:
    """1つのImageEntry"""
    return create_image_entry("tests/data/images/test1.jpg", hash_value="a" * 64)


@pytest.fixture
def image_entry_two() -> ImageEntry:
    """2つ目のImageEntry"""
    return create_image_entry("tests/data/images/test2.jpg", hash_value="b" * 64)


@pytest.fixture
def image_entry_three() -> ImageEntry:
    """3つ目のImageEntry"""
    return create_image_entry("tests/data/images/test3.jpg", hash_value="c" * 64)


@pytest.fixture
def image_entries_many(
    image_entry_one: ImageEntry,
    image_entry_two: ImageEntry,
    image_entry_three: ImageEntry,
) -> list[ImageEntry]:
    """複数のImageEntry"""
    return [image_entry_one, image_entry_two, image_entry_three]


# ----------------------------
# Helper functions
# ----------------------------


# ----------------------------
# Test classes
# ----------------------------


class TestDuckDBImagesRepositoryValid:
    """正常系のテスト

    テストケース:
        -add
            - 1件の画像を追加する: test_add_one_image
            - 複数件の画像を追加する: test_add_many_images
            - 空のリストが入力された場合: test_add_empty_list
        - remove
            - 1件の画像を削除する: test_remove_one_image
            - 複数件の画像を削除する: test_remove_many_images
            - 存在しない画像IDを指定した場合: test_remove_nonexistent_image
        - get
            - 存在する画像IDを指定した場合: test_get_existing_image
            - 存在しない画像IDを指定した場合: test_get_nonexistent_image
        - find_by_hashes
            - 存在するハッシュを指定した場合: test_find_by_hashes_existing
            - 存在しないハッシュを指定した場合: test_find_by_hashes_nonexistent
        - update
            - 1件の画像を更新する: test_update_one_image
            - 複数件の画像を更新する: test_update_many_images
            - 空のリストが入力された場合: test_update_empty_list
        - contains
            - 存在する画像IDを指定した場合: test_contains_existing_image
            - 存在しない画像IDを指定した場合: test_contains_nonexistent_image
    """

    def test_add_one_image(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """1件の画像を追加する"""
        # 実行
        result = repository.add(image_entry_one)

        # 検証
        assert len(result) == 1
        assert result[0] == 1  # 最初のIDは1

        # データベースに保存されているか確認
        retrieved = repository.get(result[0])
        assert retrieved is not None
        assert retrieved.image_id == result[0]
        assert str(retrieved.file_location) == str(image_entry_one.file_location)
        assert retrieved.width == image_entry_one.width
        assert retrieved.height == image_entry_one.height
        assert retrieved.file_type == image_entry_one.file_type
        assert str(retrieved.hash) == str(image_entry_one.hash)
        assert retrieved.file_size == image_entry_one.file_size

    def test_add_many_images(self, repository: DuckDBImagesRepository, image_entries_many: list[ImageEntry]) -> None:
        """複数件の画像を追加する"""
        # 実行
        result = repository.add(image_entries_many)

        # 検証
        expected_count = 3
        assert len(result) == expected_count
        assert result == [1, 2, 3]

        # データベースに保存されているか確認
        for i, entry in enumerate(image_entries_many):
            retrieved = repository.get(result[i])
            assert retrieved is not None
            assert str(retrieved.hash) == str(entry.hash)

    def test_add_empty_list(self, repository: DuckDBImagesRepository) -> None:
        """空のリストが入力された場合"""
        # 実行
        result = repository.add([])

        # 検証
        assert result == []

    def test_remove_one_image(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """1件の画像を削除する"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entry_one)
        image_id = image_ids[0]

        # 削除前に存在することを確認
        assert repository.contains(image_id) is True

        # 実行
        repository.remove(image_id)

        # 検証
        assert repository.contains(image_id) is False
        assert repository.get(image_id) is None

    def test_remove_many_images(self, repository: DuckDBImagesRepository, image_entries_many: list[ImageEntry]) -> None:
        """複数件の画像を削除する"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entries_many)

        # 削除前に存在することを確認
        for image_id in image_ids:
            assert repository.contains(image_id) is True

        # 実行
        repository.remove(image_ids)

        # 検証
        for image_id in image_ids:
            assert repository.contains(image_id) is False
            assert repository.get(image_id) is None

    def test_remove_nonexistent_image(self, repository: DuckDBImagesRepository) -> None:
        """存在しない画像IDを指定した場合"""
        # 実行（エラーが発生しないことを確認）
        # DuckDBのDELETEは存在しないIDでもエラーを発生させない
        repository.remove(999)

        # 複数の存在しないIDでもエラーが発生しないことを確認
        repository.remove([999, 1000, 1001])

    def test_get_existing_image(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """存在する画像IDを指定した場合"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entry_one)
        image_id = image_ids[0]

        # 実行
        retrieved = repository.get(image_id)

        # 検証
        assert retrieved is not None
        assert retrieved.image_id == image_id
        assert str(retrieved.hash) == str(image_entry_one.hash)

    def test_get_nonexistent_image(self, repository: DuckDBImagesRepository) -> None:
        """存在しない画像IDを指定した場合"""
        # 実行
        retrieved = repository.get(999)

        # 検証
        assert retrieved is None

    def test_find_by_hashes_existing(
        self,
        repository: DuckDBImagesRepository,
        image_entries_many: list[ImageEntry],
    ) -> None:
        """存在するハッシュを指定した場合"""
        # セットアップ: 画像を追加
        repository.add(image_entries_many)

        # 実行: 1つのハッシュで検索
        hash_to_find = image_entries_many[0].hash
        result = repository.find_by_hashes(hash_to_find)

        # 検証
        assert len(result) == 1
        assert str(result[0].hash) == str(hash_to_find)

        # 実行: 複数のハッシュで検索
        hashes_to_find = [entry.hash for entry in image_entries_many[:2]]
        result = repository.find_by_hashes(hashes_to_find)

        # 検証
        expected_count = 2
        assert len(result) == expected_count
        found_hashes = {str(r.hash) for r in result}
        expected_hashes = {str(h) for h in hashes_to_find}
        assert found_hashes == expected_hashes

    def test_find_by_hashes_nonexistent(self, repository: DuckDBImagesRepository) -> None:
        """存在しないハッシュを指定した場合"""
        # 実行
        nonexistent_hash = ImageHash("a" * 64)
        result = repository.find_by_hashes(nonexistent_hash)

        # 検証
        assert result == []

        # 実行: 空のリスト
        result = repository.find_by_hashes([])

        # 検証
        assert result == []

    def test_update_one_image(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """1件の画像を更新する"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entry_one)
        image_id = image_ids[0]

        # 更新用のエントリを作成
        updated_width = 3840
        updated_height = 2160
        updated_entry = ImageEntry(
            image_id=image_id,
            file_location=FileLocation("tests/data/images/updated.jpg"),
            width=updated_width,
            height=updated_height,
            file_type="png",
            hash=image_entry_one.hash,  # ハッシュは変更しない
            file_size=2048 * 1024,
            added_at=None,
            updated_at=None,
        )

        # 実行
        repository.update([updated_entry])

        # 検証
        retrieved = repository.get(image_id)
        assert retrieved is not None
        assert str(retrieved.file_location) == "tests/data/images/updated.jpg"
        assert retrieved.width == updated_width
        assert retrieved.height == updated_height
        assert retrieved.file_type == "png"
        assert retrieved.file_size == 2048 * 1024

    def test_update_many_images(self, repository: DuckDBImagesRepository, image_entries_many: list[ImageEntry]) -> None:
        """複数件の画像を更新する"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entries_many)

        # 更新用のエントリを作成
        updated_width = 3840
        updated_height = 2160
        updated_entries = [
            ImageEntry(
                image_id=image_id,
                file_location=FileLocation(f"tests/data/images/updated_{i}.jpg"),
                width=updated_width,
                height=updated_height,
                file_type="png",
                hash=entry.hash,  # ハッシュは変更しない
                file_size=2048 * 1024,
                added_at=None,
                updated_at=None,
            )
            for i, (image_id, entry) in enumerate(
                zip(image_ids, image_entries_many, strict=True),
            )
        ]

        # 実行
        repository.update(updated_entries)

        # 検証
        for i, image_id in enumerate(image_ids):
            retrieved = repository.get(image_id)
            assert retrieved is not None
            assert str(retrieved.file_location) == f"tests/data/images/updated_{i}.jpg"
            assert retrieved.width == updated_width
            assert retrieved.height == updated_height
            assert retrieved.file_type == "png"

    def test_update_nonexistent_image(self, repository: DuckDBImagesRepository) -> None:
        """存在しない画像IDを指定した場合"""
        # 存在しないIDのエントリを作成
        nonexistent_entry = ImageEntry(
            image_id=999,
            file_location=FileLocation("tests/data/images/nonexistent.jpg"),
            width=1920,
            height=1080,
            file_type="jpg",
            hash=ImageHash("a" * 64),
            file_size=1024 * 1024,
            added_at=None,
            updated_at=None,
        )

        # 実行（エラーが発生しないことを確認）
        # DuckDBのUPDATEは存在しないIDでもエラーを発生させない（更新行数が0になるだけ）
        repository.update([nonexistent_entry])

        # 検証: 画像が追加されていないことを確認
        assert repository.get(999) is None

    def test_contains_existing_image(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """存在する画像IDを指定した場合"""
        # セットアップ: 画像を追加
        image_ids = repository.add(image_entry_one)
        image_id = image_ids[0]

        # 実行
        result = repository.contains(image_id)

        # 検証
        assert result is True

    def test_contains_nonexistent_image(self, repository: DuckDBImagesRepository) -> None:
        """存在しない画像IDを指定した場合"""
        # 実行
        result = repository.contains(999)

        # 検証
        assert result is False


class TestDuckDBImagesRepositoryInvalid:
    """異常系のテスト

    テストケース:
        - add
            - 重複するハッシュが存在する場合: test_add_duplicate_hash
        - remove
            - 空のリストが入力された場合: test_remove_empty_list
        - get
        - find_by_hashes
        - update
            - 存在しない画像IDを指定した場合: test_update_nonexistent_image
    """

    def test_add_duplicate_hash(self, repository: DuckDBImagesRepository, image_entry_one: ImageEntry) -> None:
        """重複するハッシュが存在する場合"""
        # セットアップ: 最初の画像を追加
        repository.add(image_entry_one)

        # 同じハッシュを持つ別の画像を作成
        duplicate_entry = create_image_entry(
            "tests/data/images/duplicate.jpg",
            hash_value=str(image_entry_one.hash),  # 同じハッシュ
        )

        # 実行 & 検証
        with pytest.raises(DuplicateImageError):
            repository.add(duplicate_entry)

    def test_remove_empty_list(self, repository: DuckDBImagesRepository) -> None:
        """空のリストが入力された場合"""
        with pytest.raises(ValueError):
            repository.remove([])

    def test_update_empty_list(self, repository: DuckDBImagesRepository) -> None:
        """空のリストが入力された場合"""
        with pytest.raises(ValueError):
            repository.update([])
