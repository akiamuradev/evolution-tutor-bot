-- Инициализация базы данных ЭВО:ЛЮЦИЯ

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    tg_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    consent_given BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP,
    parent_consent BOOLEAN DEFAULT FALSE,
    parent_consent_date TIMESTAMP,
    preferred_model VARCHAR(50) DEFAULT 'standard',
    voice_enabled BOOLEAN DEFAULT TRUE,
    grade VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предметов
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

-- Таблица заданий ФИПИ
CREATE TABLE IF NOT EXISTS fipi_tasks (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id),
    year INTEGER,
    task_number INTEGER,
    difficulty VARCHAR(20),
    topic TEXT,
    subtopic TEXT,
    condition TEXT,
    solution TEXT,
    answer TEXT,
    explanation TEXT,
    source_url TEXT
);

-- Таблица прогресса ученика (НОВАЯ СТРУКТУРА)
CREATE TABLE IF NOT EXISTS student_progress (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    task_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    topic TEXT,
    user_answer TEXT,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    used_explanation BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES fipi_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_student_progress_user ON student_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_subject ON student_progress(subject_id);
CREATE INDEX IF NOT EXISTS idx_student_progress_topic ON student_progress(topic);
CREATE INDEX IF NOT EXISTS idx_student_progress_created ON student_progress(created_at);
CREATE INDEX IF NOT EXISTS idx_fipi_tasks_subject ON fipi_tasks(subject_id);
CREATE INDEX IF NOT EXISTS idx_fipi_tasks_task_number ON fipi_tasks(task_number);
CREATE INDEX IF NOT EXISTS idx_fipi_tasks_topic ON fipi_tasks(topic);
CREATE INDEX IF NOT EXISTS idx_fipi_tasks_search_fts
ON fipi_tasks
USING GIN (to_tsvector('simple',
    COALESCE(condition, '') || ' ' ||
    COALESCE(topic, '') || ' ' ||
    COALESCE(subtopic, '') || ' ' ||
    COALESCE(answer, '')
));

-- Таблица достижений
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    achievement_type VARCHAR(50) NOT NULL,
    achievement_name VARCHAR(100) NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_type)
);

CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);

-- Таблица персональных планов
CREATE TABLE IF NOT EXISTS study_plans (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    plan_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days')
);

CREATE INDEX IF NOT EXISTS idx_study_plans_user ON study_plans(user_id);
