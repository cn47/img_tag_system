import duckdb
import pytest

from domain.entities.model_tag import ModelTagEntries, ModelTagEntry
from infrastructure.repositories.model_tag.duck_db import DuckDBModelTagRepository


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

        CREATE TABLE IF NOT EXISTS tags_camie_v2 (
            image_id  INTEGER NOT NULL REFERENCES images(image_id),
            category  TEXT NOT NULL,
            tag       TEXT NOT NULL,
            score     DOUBLE,
            archived  BOOLEAN DEFAULT FALSE,
            PRIMARY KEY(image_id, category, tag)
        );
        """
    )
    # テスト用の画像データを1つ作成
    conn.execute(
        """
        INSERT INTO images (image_id, file_location, hash) VALUES (1, '/test/image1.jpg', 'hash1');
        INSERT INTO images (image_id, file_location, hash) VALUES (2, '/test/image2.jpg', 'hash2');
        """
    )
    yield conn
    conn.close()


@pytest.fixture
def repository(db_connection):
    """DuckDBModelTagRepositoryのインスタンスを作成"""
    return DuckDBModelTagRepository(db_connection, model_name="camie_v2")


@pytest.fixture
def sample_tag_entries():
    """テスト用のサンプルModelTagEntriesを作成"""
    return ModelTagEntries(
        entries=[
            ModelTagEntry(
                image_id=1,
                category="general",
                tag="tag1",
                score=0.95,
                archived=False,
            ),
            ModelTagEntry(
                image_id=1,
                category="rating",
                tag="safe",
                score=0.98,
                archived=False,
            ),
            ModelTagEntry(
                image_id=1,
                category="character",
                tag="character1",
                score=0.85,
                archived=False,
            ),
        ]
    )


@pytest.fixture
def sample_single_tag_entry():
    """テスト用の単一タグエントリを作成"""
    return ModelTagEntries(
        entries=[
            ModelTagEntry(
                image_id=1,
                category="general",
                tag="single_tag",
                score=0.90,
                archived=False,
            )
        ]
    )


class TestInsertMany:
    """insert_manyメソッドのテスト"""

    def test_insert_many_success(self, repository, sample_tag_entries):
        """正常系: 複数タグの挿入が成功する"""
        repository.insert_many(sample_tag_entries)

        # 挿入されたタグを確認
        result = repository.list_by_image(1)
        assert len(result.entries) == 3

        # 各タグが正しく挿入されているか確認
        tag_dict = {(e.category, e.tag): e for e in result.entries}
        assert ("general", "tag1") in tag_dict
        assert ("rating", "safe") in tag_dict
        assert ("character", "character1") in tag_dict

        entry1 = tag_dict[("general", "tag1")]
        assert entry1.image_id == 1
        assert entry1.score == 0.95
        assert entry1.archived is False

    def test_insert_many_empty_entries(self, repository):
        """正常系: 空のエントリリストを挿入してもエラーにならない"""
        empty_entries = ModelTagEntries(entries=[])
        repository.insert_many(empty_entries)

        # 何も挿入されていないことを確認
        result = repository.list_by_image(1)
        assert len(result.entries) == 0

    def test_insert_many_single_entry(self, repository, sample_single_tag_entry):
        """正常系: 単一タグの挿入が成功する"""
        repository.insert_many(sample_single_tag_entry)

        result = repository.list_by_image(1)
        assert len(result.entries) == 1
        assert result.entries[0].category == "general"
        assert result.entries[0].tag == "single_tag"
        assert result.entries[0].score == 0.90

    def test_insert_many_duplicate_key_raises_error(self, repository, sample_tag_entries):
        """異常系: 重複したキー（image_id, category, tag）で挿入するとエラーが発生する"""
        # 最初の挿入は成功
        repository.insert_many(sample_tag_entries)

        # 同じキーで再度挿入するとエラー
        duplicate_entries = ModelTagEntries(
            entries=[
                ModelTagEntry(
                    image_id=1,
                    category="general",
                    tag="tag1",
                    score=0.99,  # 異なるスコアでもエラーになる
                    archived=False,
                )
            ]
        )

        with pytest.raises(duckdb.ConstraintException):
            repository.insert_many(duplicate_entries)

    def test_insert_many_invalid_image_id_raises_error(self, repository):
        """異常系: 存在しないimage_idで挿入するとエラーが発生する"""
        invalid_entries = ModelTagEntries(
            entries=[
                ModelTagEntry(
                    image_id=999,  # 存在しないimage_id
                    category="general",
                    tag="tag1",
                    score=0.95,
                    archived=False,
                )
            ]
        )

        with pytest.raises(duckdb.ConstraintException):
            repository.insert_many(invalid_entries)

    def test_insert_many_multiple_images(self, repository):
        """正常系: 複数の画像にタグを挿入できる"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=False),
                ModelTagEntry(image_id=2, category="general", tag="tag2", score=0.8, archived=False),
            ]
        )

        repository.insert_many(entries)

        result1 = repository.list_by_image(1)
        result2 = repository.list_by_image(2)

        assert len(result1.entries) == 1
        assert result1.entries[0].tag == "tag1"
        assert len(result2.entries) == 1
        assert result2.entries[0].tag == "tag2"


class TestListByImage:
    """list_by_imageメソッドのテスト"""

    def test_list_by_image_success(self, repository, sample_tag_entries):
        """正常系: 存在する画像IDでタグを取得できる"""
        repository.insert_many(sample_tag_entries)

        result = repository.list_by_image(1)

        assert isinstance(result, ModelTagEntries)
        assert len(result.entries) == 3

        # 各エントリが正しく変換されているか確認
        for entry in result.entries:
            assert isinstance(entry, ModelTagEntry)
            assert entry.image_id == 1
            assert isinstance(entry.category, str)
            assert isinstance(entry.tag, str)
            assert isinstance(entry.score, float)
            assert isinstance(entry.archived, bool)

    def test_list_by_image_empty_result(self, repository):
        """正常系: タグが存在しない画像IDで空のリストが返る"""
        result = repository.list_by_image(1)

        assert isinstance(result, ModelTagEntries)
        assert len(result.entries) == 0

    def test_list_by_image_nonexistent_image_id(self, repository):
        """正常系: 存在しない画像IDで空のリストが返る"""
        result = repository.list_by_image(999)

        assert isinstance(result, ModelTagEntries)
        assert len(result.entries) == 0

    def test_list_by_image_archived_tags_included(self, repository):
        """正常系: アーカイブされたタグも取得される"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=False),
                ModelTagEntry(image_id=1, category="general", tag="tag2", score=0.8, archived=True),
            ]
        )
        repository.insert_many(entries)

        result = repository.list_by_image(1)

        assert len(result.entries) == 2
        archived_tags = [e for e in result.entries if e.archived]
        assert len(archived_tags) == 1
        assert archived_tags[0].tag == "tag2"

    def test_list_by_image_returns_correct_order(self, repository):
        """正常系: 複数タグが正しい順序で返る（DBの順序に依存）"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="a", tag="tag1", score=0.9, archived=False),
                ModelTagEntry(image_id=1, category="b", tag="tag2", score=0.8, archived=False),
                ModelTagEntry(image_id=1, category="c", tag="tag3", score=0.7, archived=False),
            ]
        )
        repository.insert_many(entries)

        result = repository.list_by_image(1)

        assert len(result.entries) == 3
        # すべてのタグが含まれていることを確認
        tags = {(e.category, e.tag) for e in result.entries}
        assert ("a", "tag1") in tags
        assert ("b", "tag2") in tags
        assert ("c", "tag3") in tags


class TestDeleteAllByImage:
    """delete_all_by_imageメソッドのテスト"""

    def test_delete_all_by_image_success(self, repository, sample_tag_entries):
        """正常系: 存在する画像のタグをすべて削除できる"""
        repository.insert_many(sample_tag_entries)

        # 削除前にタグが存在することを確認
        result_before = repository.list_by_image(1)
        assert len(result_before.entries) == 3

        repository.delete_all_by_image(1)

        # 削除後にタグが存在しないことを確認
        result_after = repository.list_by_image(1)
        assert len(result_after.entries) == 0

    def test_delete_all_by_image_empty_image(self, repository):
        """正常系: タグが存在しない画像IDで削除してもエラーにならない"""
        # エラーが発生しないことを確認
        repository.delete_all_by_image(1)

    def test_delete_all_by_image_nonexistent_image_id(self, repository):
        """正常系: 存在しない画像IDで削除してもエラーにならない"""
        # エラーが発生しないことを確認
        repository.delete_all_by_image(999)

    def test_delete_all_by_image_only_target_image(self, repository):
        """正常系: 指定した画像のタグのみが削除され、他の画像のタグは残る"""
        # 画像1と画像2にタグを挿入
        entries1 = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=False),
                ModelTagEntry(image_id=1, category="general", tag="tag2", score=0.8, archived=False),
            ]
        )
        entries2 = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=2, category="general", tag="tag3", score=0.9, archived=False),
            ]
        )

        repository.insert_many(entries1)
        repository.insert_many(entries2)

        # 画像1のタグを削除
        repository.delete_all_by_image(1)

        # 画像1のタグが削除されていることを確認
        result1 = repository.list_by_image(1)
        assert len(result1.entries) == 0

        # 画像2のタグが残っていることを確認
        result2 = repository.list_by_image(2)
        assert len(result2.entries) == 1
        assert result2.entries[0].tag == "tag3"


class TestArchiveTag:
    """archive_tagメソッドのテスト"""

    def test_archive_tag_success(self, repository):
        """正常系: 存在するタグをアーカイブできる"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=False),
            ]
        )
        repository.insert_many(entries)

        # アーカイブ前の状態を確認
        result_before = repository.list_by_image(1)
        assert result_before.entries[0].archived is False

        repository.archive_tag(1, "general", "tag1")

        # アーカイブ後の状態を確認
        result_after = repository.list_by_image(1)
        assert len(result_after.entries) == 1
        assert result_after.entries[0].archived is True
        assert result_after.entries[0].tag == "tag1"
        assert result_after.entries[0].score == 0.9  # スコアは変更されない

    def test_archive_tag_multiple_tags(self, repository, sample_tag_entries):
        """正常系: 複数タグがある場合、指定したタグのみがアーカイブされる"""
        repository.insert_many(sample_tag_entries)

        # 1つのタグのみをアーカイブ
        repository.archive_tag(1, "general", "tag1")

        result = repository.list_by_image(1)

        # アーカイブされたタグを確認
        archived_tags = [e for e in result.entries if e.archived]
        non_archived_tags = [e for e in result.entries if not e.archived]

        assert len(archived_tags) == 1
        assert archived_tags[0].tag == "tag1"
        assert len(non_archived_tags) == 2

    def test_archive_tag_nonexistent_tag_no_error(self, repository):
        """正常系: 存在しないタグをアーカイブしてもエラーにならない"""
        # エラーが発生しないことを確認
        repository.archive_tag(1, "general", "nonexistent_tag")

        # 何も変更されていないことを確認
        result = repository.list_by_image(1)
        assert len(result.entries) == 0

    def test_archive_tag_nonexistent_image_id_no_error(self, repository):
        """正常系: 存在しない画像IDでアーカイブしてもエラーにならない"""
        # エラーが発生しないことを確認
        repository.archive_tag(999, "general", "tag1")

    def test_archive_tag_already_archived(self, repository):
        """正常系: 既にアーカイブされたタグを再度アーカイブしてもエラーにならない"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=True),
            ]
        )
        repository.insert_many(entries)

        # 既にアーカイブされているタグを再度アーカイブ
        repository.archive_tag(1, "general", "tag1")

        # アーカイブ状態が維持されていることを確認
        result = repository.list_by_image(1)
        assert result.entries[0].archived is True

    def test_archive_tag_wrong_category(self, repository):
        """正常系: 異なるカテゴリのタグはアーカイブされない"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=False),
                ModelTagEntry(image_id=1, category="rating", tag="tag1", score=0.8, archived=False),
            ]
        )
        repository.insert_many(entries)

        # generalカテゴリのtag1のみをアーカイブ
        repository.archive_tag(1, "general", "tag1")

        result = repository.list_by_image(1)

        # generalカテゴリのtag1がアーカイブされていることを確認
        general_tag = next(e for e in result.entries if e.category == "general" and e.tag == "tag1")
        rating_tag = next(e for e in result.entries if e.category == "rating" and e.tag == "tag1")

        assert general_tag.archived is True
        assert rating_tag.archived is False


class TestRowToEntity:
    """_row_to_entityメソッドのテスト（内部メソッドの間接的テスト）"""

    def test_row_to_entity_conversion(self, repository, sample_tag_entries):
        """正常系: tupleが正しくModelTagEntryに変換される"""
        repository.insert_many(sample_tag_entries)

        result = repository.list_by_image(1)

        assert len(result.entries) > 0
        for entry in result.entries:
            assert isinstance(entry, ModelTagEntry)
            assert isinstance(entry.image_id, int)
            assert isinstance(entry.category, str)
            assert isinstance(entry.tag, str)
            assert isinstance(entry.score, float)
            assert isinstance(entry.archived, bool)

    def test_row_to_entity_archived_flag(self, repository):
        """正常系: archivedフラグが正しく変換される"""
        entries = ModelTagEntries(
            entries=[
                ModelTagEntry(image_id=1, category="general", tag="tag1", score=0.9, archived=True),
            ]
        )
        repository.insert_many(entries)

        result = repository.list_by_image(1)

        assert result.entries[0].archived is True
