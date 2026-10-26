-- 階段 1：成語資料表（只在 dev 專案執行；正式環境見 DEPLOY_CHECKLIST.md）
-- 可重複執行。後端使用 service_role key（會略過 RLS），因此所有表開 RLS 但不設 policy。

-- ── scores（既有表；dev 專案若尚未建立才會建立）────────────────
CREATE TABLE IF NOT EXISTS scores (
    id         BIGSERIAL PRIMARY KEY,
    class_name TEXT,
    seat_no    INTEGER,
    name       TEXT        NOT NULL,
    score      INTEGER     NOT NULL,
    total      INTEGER     NOT NULL DEFAULT 100,
    duration   INTEGER     NOT NULL DEFAULT 0,
    grade      TEXT,
    created_at TIMESTAMPTZ          DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scores_score ON scores (score DESC, created_at ASC);

-- ── idioms ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS idioms (
    id             BIGSERIAL PRIMARY KEY,
    grade          TEXT   NOT NULL CHECK (grade IN ('elementary_low', 'elementary_high', 'junior')),
    idiom          TEXT   NOT NULL CHECK (idiom = btrim(idiom) AND idiom <> ''),
    meaning        TEXT   NOT NULL DEFAULT '',
    explanation    TEXT   NOT NULL DEFAULT '',

    -- 與現有 JSON 的 "questions" 完全相同：{typo, compose, application, teaching?}
    questions      JSONB  NOT NULL DEFAULT '{}'::jsonb,

    -- 教育部《成語典》原文（獨立保存，不與教師編輯內容混在一起）
    moe_definition TEXT,
    moe_notes      TEXT,
    moe_usage      TEXT,

    -- 逐欄位來源，例如 {"meaning":"moe","teaching.plain":"ai"}（階段 5 使用）
    field_sources  JSONB  NOT NULL DEFAULT '{}'::jsonb,

    status         TEXT   NOT NULL DEFAULT 'draft'     CHECK (status IN ('draft', 'published')),
    source         TEXT   NOT NULL DEFAULT 'teacher'   CHECK (source IN ('moe', 'ai', 'teacher')),
    created_by     BIGINT,                              -- 階段 2 建立 teachers 表後再加外鍵
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (grade, idiom)
);

CREATE INDEX IF NOT EXISTS idx_idioms_grade_status ON idioms (grade, status);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_idioms_updated_at ON idioms;
CREATE TRIGGER trg_idioms_updated_at
    BEFORE UPDATE ON idioms
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── RLS：開啟但不設 policy（anon / authenticated 一律讀寫不到）──
ALTER TABLE idioms ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores ENABLE ROW LEVEL SECURITY;
