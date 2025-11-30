from datetime import datetime

import duckdb
import pytest

from domain.entities.images import ImageEntry
from exceptions import DuplicateImageError
from infrastructure.repositories.images.duck_db import DuckDBImagesRepository


@pytest.fixture
def db_connection():
    """テスト用のインメモリDuckDB接続を作成"""
    conn = duckdb.connect(":memory:")
    # スキーマを作成
    conn.execute(
        """
        CREATE SEQUENCE image_id_seq START 1 INCREMENT 1;

        CREATE TABLE IF NOT EXISTS images (
            image_id       INTEGER PRIMARY KEY DEFAULT NEXTVAL('image_id_seq'),
            file_location  TEXT NOT NULL,
            width          INTEGER,
            height         INTEGER,
            file_type      TEXT,
            hash           TEXT NOT NULL UNIQUE,
            added_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    yield conn
    conn.close()


@pytest.fixture
def repository(db_connection):
    """ImagesRepositoryのインスタンスを作成"""
    return ImagesRepository(db_connection)


@pytest.fixture
def sample_image_entry():
    """テスト用のサンプルImageEntryを作成"""
    return ImageEntry(
        image_id=None,
        file_location="/path/to/image.jpg",
        width=1920,
        height=1080,
        file_type="jpg",
        hash="abc123def456",
    )


class TestSave:
    """saveメソッドのテスト"""

    def test_save_new_image_success(self, repository, sample_image_entry):
        """正常系: 新規画像の保存が成功する"""
        image_id = repository.save(sample_image_entry)

        assert image_id == 1
        assert sample_image_entry.image_id == 1

        # DBに正しく保存されているか確認
        saved = repository.get(image_id)
        assert saved is not None
        assert saved.file_location == sample_image_entry.file_location
        assert saved.width == sample_image_entry.width
        assert saved.height == sample_image_entry.height
        assert saved.file_type == sample_image_entry.file_type
        assert saved.hash == sample_image_entry.hash
        assert saved.image_id == image_id

    def test_save_duplicate_hash_raises_error(self, repository, sample_image_entry):
        """異常系: 重複したハッシュで保存するとDuplicateImageErrorが発生する"""
        # 最初の保存は成功
        repository.save(sample_image_entry)

        # 同じハッシュで再度保存するとエラー
        duplicate_entry = ImageEntry(
            image_id=None,
            file_location="/path/to/different.jpg",
            width=800,
            height=600,
            file_type="png",
            hash=sample_image_entry.hash,  # 同じハッシュ
        )

        with pytest.raises(DuplicateImageError) as exc_info:
            repository.save(duplicate_entry)

        assert "Duplicate image" in str(exc_info.value)
        assert sample_image_entry.hash in str(exc_info.value)

    def test_save_multiple_images_success(self, repository):
        """正常系: 複数の異なる画像を保存できる"""
        entries = [
            ImageEntry(
                image_id=None,
                file_location=f"/path/to/image{i}.jpg",
                width=100 + i,
                height=100 + i,
                file_type="jpg",
                hash=f"hash{i}",
            )
            for i in range(5)
        ]

        image_ids = [repository.save(entry) for entry in entries]

        # 各IDが異なることを確認
        assert len(set(image_ids)) == 5
        assert image_ids == [1, 2, 3, 4, 5]

        # すべて保存されていることを確認
        assert repository.count() == 5


class TestGet:
    """getメソッドのテスト"""

    def test_get_existing_image_success(self, repository, sample_image_entry):
        """正常系: 存在する画像IDで取得できる"""
        image_id = repository.save(sample_image_entry)
        result = repository.get(image_id)

        assert result is not None
        assert result.image_id == image_id
        assert result.file_location == sample_image_entry.file_location
        assert result.hash == sample_image_entry.hash

    def test_get_nonexistent_image_returns_none(self, repository):
        """異常系: 存在しない画像IDで取得するとNoneが返る"""
        result = repository.get(999)
        assert result is None


class TestDelete:
    """deleteメソッドのテスト"""

    def test_delete_existing_image_success(self, repository, sample_image_entry):
        """正常系: 存在する画像を削除できる"""
        image_id = repository.save(sample_image_entry)
        assert repository.exists(image_id) is True

        repository.delete(image_id)

        assert repository.exists(image_id) is False
        assert repository.get(image_id) is None

    def test_delete_nonexistent_image_no_error(self, repository):
        """正常系: 存在しない画像を削除してもエラーにならない"""
        # エラーが発生しないことを確認
        repository.delete(999)


class TestExists:
    """existsメソッドのテスト"""

    def test_exists_true_for_existing_image(self, repository, sample_image_entry):
        """正常系: 存在する画像IDでTrueが返る"""
        image_id = repository.save(sample_image_entry)
        assert repository.exists(image_id) is True

    def test_exists_false_for_nonexistent_image(self, repository):
        """正常系: 存在しない画像IDでFalseが返る"""
        assert repository.exists(999) is False


class TestCount:
    """countメソッドのテスト"""

    def test_count_empty_database_returns_zero(self, repository):
        """正常系: 空のデータベースで0が返る"""
        assert repository.count() == 0

    def test_count_returns_correct_number(self, repository):
        """正常系: 正しいレコード数が返る"""
        entries = [
            ImageEntry(
                image_id=None,
                file_location=f"/path/to/image{i}.jpg",
                width=100,
                height=100,
                file_type="jpg",
                hash=f"hash{i}",
            )
            for i in range(3)
        ]

        for entry in entries:
            repository.save(entry)

        assert repository.count() == 3

    def test_count_after_delete(self, repository, sample_image_entry):
        """正常系: 削除後のレコード数が正しい"""
        image_id = repository.save(sample_image_entry)
        assert repository.count() == 1

        repository.delete(image_id)
        assert repository.count() == 0


class TestUpdateLocation:
    """update_locationメソッドのテスト"""

    def test_update_location_success(self, repository, sample_image_entry):
        """正常系: ファイルパスを更新できる"""
        image_id = repository.save(sample_image_entry)
        new_location = "/new/path/to/image.jpg"

        repository.update_location(image_id, new_location)

        updated = repository.get(image_id)
        assert updated is not None
        assert updated.file_location == new_location
        assert updated.updated_at is not None
        # updated_atが更新されていることを確認（added_atより後）
        assert updated.updated_at >= updated.added_at

    def test_update_location_nonexistent_image_no_error(self, repository):
        """正常系: 存在しない画像IDで更新してもエラーにならない"""
        # エラーが発生しないことを確認
        repository.update_location(999, "/new/path.jpg")


class TestFindByHash:
    """find_by_hashメソッドのテスト"""

    def test_find_by_hash_existing_success(self, repository, sample_image_entry):
        """正常系: 存在するハッシュで取得できる"""
        repository.save(sample_image_entry)
        result = repository.find_by_hash(sample_image_entry.hash)

        assert result is not None
        assert result.hash == sample_image_entry.hash
        assert result.file_location == sample_image_entry.file_location

    def test_find_by_hash_nonexistent_returns_none(self, repository):
        """正常系: 存在しないハッシュでNoneが返る"""
        result = repository.find_by_hash("nonexistent_hash")
        assert result is None

    def test_find_by_hash_returns_correct_image(self, repository):
        """正常系: 複数画像がある場合、正しい画像が返る"""
        entries = [
            ImageEntry(
                image_id=None,
                file_location=f"/path/to/image{i}.jpg",
                width=100,
                height=100,
                file_type="jpg",
                hash=f"hash{i}",
            )
            for i in range(3)
        ]

        for entry in entries:
            repository.save(entry)

        # 2番目のエントリを検索
        result = repository.find_by_hash("hash1")
        assert result is not None
        assert result.hash == "hash1"
        assert result.file_location == "/path/to/image1.jpg"


class TestGetAllFileLocations:
    """get_all_file_locationsメソッドのテスト"""

    def test_get_all_file_locations_empty_returns_empty_dict(self, repository):
        """正常系: 空のデータベースで空の辞書が返る"""
        result = repository.get_all_file_locations()
        assert result == {}

    def test_get_all_file_locations_returns_all_locations(self, repository):
        """正常系: すべてのファイルパスが返る"""
        entries = [
            ImageEntry(
                image_id=None,
                file_location=f"/path/to/image{i}.jpg",
                width=100,
                height=100,
                file_type="jpg",
                hash=f"hash{i}",
            )
            for i in range(3)
        ]

        image_ids = [repository.save(entry) for entry in entries]

        result = repository.get_all_file_locations()

        assert len(result) == 3
        assert result[image_ids[0]] == "/path/to/image0.jpg"
        assert result[image_ids[1]] == "/path/to/image1.jpg"
        assert result[image_ids[2]] == "/path/to/image2.jpg"

    def test_get_all_file_locations_after_delete(self, repository):
        """正常系: 削除後のファイルパス一覧が正しい"""
        entries = [
            ImageEntry(
                image_id=None,
                file_location=f"/path/to/image{i}.jpg",
                width=100,
                height=100,
                file_type="jpg",
                hash=f"hash{i}",
            )
            for i in range(3)
        ]

        image_ids = [repository.save(entry) for entry in entries]
        repository.delete(image_ids[1])

        result = repository.get_all_file_locations()

        assert len(result) == 2
        assert image_ids[0] in result
        assert image_ids[1] not in result
        assert image_ids[2] in result


class TestRowToEntity:
    """_row_to_entityメソッドのテスト（内部メソッドの間接的テスト）"""

    def test_row_to_entity_conversion(self, repository, sample_image_entry):
        """正常系: tupleが正しくImageEntryに変換される"""
        image_id = repository.save(sample_image_entry)
        result = repository.get(image_id)

        assert result is not None
        assert isinstance(result, ImageEntry)
        assert result.image_id == image_id
        assert result.file_location == sample_image_entry.file_location
        assert result.width == sample_image_entry.width
        assert result.height == sample_image_entry.height
        assert result.file_type == sample_image_entry.file_type
        assert result.hash == sample_image_entry.hash
        assert isinstance(result.added_at, datetime)
        assert isinstance(result.updated_at, datetime)
