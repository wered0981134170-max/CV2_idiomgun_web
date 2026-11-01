-- 階段 2a：學校、教師帳號、登入失敗紀錄、idioms 加 school_id
-- 只在 dev 專案執行；可重複執行。需要 PostgreSQL 15+（UNIQUE NULLS NOT DISTINCT）。
-- 後端使用 service_role key，所有表開 RLS 但不設 policy。

CREATE TABLE IF NOT EXISTS schools (
    id         BIGSERIAL PRIMARY KEY,
    name       TEXT        NOT NULL UNIQUE CHECK (name = btrim(name) AND name <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teachers (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT        NOT NULL CHECK (email = lower(btrim(email)) AND email <> ''),
    password_hash TEXT        NOT NULL,
    name          TEXT        NOT NULL,
    role          TEXT        NOT NULL DEFAULT 'teacher' CHECK (role IN ('admin', 'teacher')),
    school_id     BIGINT      REFERENCES schools(id) ON DELETE RESTRICT,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- 一般教師一定要有學校；admin 可以不屬於任何學校
    CONSTRAINT teacher_needs_school CHECK (role = 'admin' OR school_id IS NOT NULL)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_teachers_email ON teachers (email);

-- 登入失敗次數限制用（存在資料庫，gunicorn 多個 worker 才會共用計數）
CREATE TABLE IF NOT EXISTS login_attempts (
    id         BIGSERIAL PRIMARY KEY,
    email      TEXT        NOT NULL,
    ip         TEXT        NOT NULL,
    success    BOOLEAN     NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts (email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip    ON login_attempts (ip, created_at DESC);

-- ── idioms：支援多校 ─────────────────────────────────────────
-- school_id 為 NULL = 共用題庫（只有 admin 能編輯）；非 NULL = 該校教師新增的成語
ALTER TABLE idioms ADD COLUMN IF NOT EXISTS school_id BIGINT REFERENCES schools(id) ON DELETE RESTRICT;
ALTER TABLE idioms DROP CONSTRAINT IF EXISTS idioms_grade_idiom_key;
ALTER TABLE idioms DROP CONSTRAINT IF EXISTS idioms_school_grade_idiom_key;
ALTER TABLE idioms ADD CONSTRAINT idioms_school_grade_idiom_key
    UNIQUE NULLS NOT DISTINCT (school_id, grade, idiom);
CREATE INDEX IF NOT EXISTS idx_idioms_school ON idioms (school_id, grade, status);

-- 階段 1 預留的 created_by 補上外鍵
ALTER TABLE idioms DROP CONSTRAINT IF EXISTS idioms_created_by_fkey;
ALTER TABLE idioms ADD CONSTRAINT idioms_created_by_fkey
    FOREIGN KEY (created_by) REFERENCES teachers(id) ON DELETE SET NULL;

ALTER TABLE schools        ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;
