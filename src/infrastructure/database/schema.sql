CREATE SEQUENCE image_id_seq START 1 INCREMENT 1;

-----------------------------------
-- 画像データテーブル
-----------------------------------
CREATE TABLE IF NOT EXISTS images (
    image_id       INTEGER PRIMARY KEY DEFAULT NEXTVAL('image_id_seq'),
    file_location  TEXT NOT NULL,
    width          INTEGER,
    height         INTEGER,
    file_type      TEXT,
    hash           TEXT NOT NULL UNIQUE,
    file_size      INTEGER,
    added_at       TIMESTAMP DEFAULT NOW(),
    updated_at     TIMESTAMP DEFAULT NOW(),
);

COMMENT ON TABLE images IS '画像ごとのメタデータを格納するテーブル';

COMMENT ON COLUMN images.image_id       IS '画像を一意に識別する ID';
COMMENT ON COLUMN images.file_location  IS '画像ファイルの保存場所（パス）';
COMMENT ON COLUMN images.width          IS '画像の横幅（ピクセル）';
COMMENT ON COLUMN images.height         IS '画像の高さ（ピクセル）';
COMMENT ON COLUMN images.file_type      IS '画像のファイルタイプ（拡張子など）';
COMMENT ON COLUMN images.hash           IS '画像のハッシュ（pHash / SHA系など）';
COMMENT ON COLUMN images.file_size      IS '画像ファイルのサイズ（バイト数）';
COMMENT ON COLUMN images.added_at       IS '画像が取り込まれた日時';
COMMENT ON COLUMN images.updated_at     IS '画像メタデータが最後に更新された日時';

-----------------------------------
-- 画像メモテーブル
-----------------------------------
CREATE TABLE IF NOT EXISTS note (
    image_id  INTEGER PRIMARY KEY REFERENCES images(image_id),
    content   TEXT
);
COMMENT ON TABLE note IS '画像ごとのメモを格納するテーブル';

COMMENT ON COLUMN note.image_id  IS '対象画像の ID（images への外部キー）';
COMMENT ON COLUMN note.content   IS 'メモ内容（UIから編集可能）';

-----------------------------------
-- 画像タグテーブル（モデルによる付与）
-----------------------------------
CREATE TABLE IF NOT EXISTS tags_camie_v2 (
    image_id  INTEGER NOT NULL REFERENCES images(image_id),
    category  TEXT NOT NULL,
    tag       TEXT NOT NULL,
    score     DOUBLE,
    archived  BOOLEAN DEFAULT FALSE,
    PRIMARY KEY(image_id, category, tag)
);

COMMENT ON TABLE tags_camie_v2 IS '画像に紐づくタグを縦持ちで管理するテーブル';

COMMENT ON COLUMN tags_camie_v2.image_id IS '対象画像の ID（images への外部キー）';
COMMENT ON COLUMN tags_camie_v2.category IS 'タグカテゴリ（general/rating/character/etc）';
COMMENT ON COLUMN tags_camie_v2.tag      IS 'タグ名';
COMMENT ON COLUMN tags_camie_v2.score    IS 'タグのスコア（モデル出力）';
COMMENT ON COLUMN tags_camie_v2.archived IS 'タグアーカイブ済みフラグ（UIから操作可能）';

CREATE INDEX IF NOT EXISTS idx_tags_camie_v2_tag_category ON tags_camie_v2 (tag, category);
CREATE INDEX IF NOT EXISTS idx_tags_camie_v2_image_id ON tags_camie_v2 (image_id);


-----------------------------------
-- 画像タグテーブル（手動による付与）
-----------------------------------
CREATE TABLE IF NOT EXISTS tags_manual (
    image_id  INTEGER NOT NULL REFERENCES images(image_id),
    category  TEXT NOT NULL,
    tag       TEXT NOT NULL,
    PRIMARY KEY(image_id, category, tag)
);

COMMENT ON TABLE tags_manual IS '画像に紐づくタグを縦持ちで管理するテーブル';

COMMENT ON COLUMN tags_manual.image_id IS '対象画像の ID（images への外部キー）';
COMMENT ON COLUMN tags_manual.category IS 'タグカテゴリ（general/rating/character/etc）';
COMMENT ON COLUMN tags_manual.tag      IS 'タグ名';

CREATE INDEX IF NOT EXISTS idx_tags_manual_tag_category ON tags_manual (tag, category);
CREATE INDEX IF NOT EXISTS idx_tags_manual_image_id ON tags_manual (image_id);