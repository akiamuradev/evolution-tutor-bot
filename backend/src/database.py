import asyncpg
import logging
import os
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def init(self):
        dsn = os.getenv("DATABASE_URL")
        self.pool = await asyncpg.create_pool(dsn)
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    tg_id BIGINT PRIMARY KEY, username VARCHAR(255), first_name VARCHAR(255),
                    consent_pd BOOLEAN DEFAULT FALSE, active_mode VARCHAR(50) DEFAULT 'standard',
                    free_requests INT DEFAULT 3,
                    student_sub BOOLEAN DEFAULT FALSE, student_expires TIMESTAMP,
                    business_sub BOOLEAN DEFAULT FALSE, business_expires TIMESTAMP,
                    standard_sub BOOLEAN DEFAULT FALSE, standard_expires TIMESTAMP,
                    total_requests INT DEFAULT 0,
                    grade_range VARCHAR(20) DEFAULT NULL, memory_notes TEXT DEFAULT '',
                    last_quiz_topic VARCHAR(100) DEFAULT NULL, voice_enabled BOOLEAN DEFAULT FALSE
                );
            """)
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_requests INT DEFAULT 0;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS grade_range VARCHAR(20) DEFAULT NULL;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS memory_notes TEXT DEFAULT '';")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_quiz_topic VARCHAR(100) DEFAULT NULL;")
            await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS voice_enabled BOOLEAN DEFAULT FALSE;")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_events (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_dialog_messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    importance SMALLINT DEFAULT 1,
                    tags TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("ALTER TABLE ai_dialog_messages ADD COLUMN IF NOT EXISTS importance SMALLINT DEFAULT 1;")
            await conn.execute("ALTER TABLE ai_dialog_messages ADD COLUMN IF NOT EXISTS tags TEXT DEFAULT '';")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_memory_profiles (
                    user_id BIGINT PRIMARY KEY,
                    summary TEXT DEFAULT '',
                    learning_profile TEXT DEFAULT '',
                    last_message_id BIGINT DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("ALTER TABLE ai_memory_profiles ADD COLUMN IF NOT EXISTS last_message_id BIGINT DEFAULT 0;")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    duration_seconds INTEGER DEFAULT 0
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_time_stats (
                    user_id BIGINT PRIMARY KEY,
                    total_seconds BIGINT DEFAULT 0,
                    session_count INTEGER DEFAULT 0,
                    longest_session_seconds INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL
                );
            """)
            await conn.execute("""
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
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS student_progress (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    task_id INTEGER NOT NULL REFERENCES fipi_tasks(id) ON DELETE CASCADE,
                    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                    topic TEXT,
                    user_answer TEXT,
                    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
                    used_explanation BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    achievement_type VARCHAR(50) NOT NULL,
                    achievement_name VARCHAR(100) NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, achievement_type)
                );
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_events_user_created ON user_events(user_id, created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_student_progress_user ON student_progress(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_student_progress_subject ON student_progress(subject_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_student_progress_topic ON student_progress(topic);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_student_progress_created ON student_progress(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fipi_tasks_subject ON fipi_tasks(subject_id);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fipi_tasks_task_number ON fipi_tasks(task_number);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_fipi_tasks_topic ON fipi_tasks(topic);")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fipi_tasks_search_fts
                ON fipi_tasks
                USING GIN (to_tsvector('simple',
                    COALESCE(condition, '') || ' ' ||
                    COALESCE(topic, '') || ' ' ||
                    COALESCE(subtopic, '') || ' ' ||
                    COALESCE(answer, '')
                ))
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_dialog_messages_user_created ON ai_dialog_messages(user_id, created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_dialog_messages_user_importance ON ai_dialog_messages(user_id, importance DESC, created_at DESC);")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_dialog_messages_fts
                ON ai_dialog_messages
                USING GIN (to_tsvector('simple', content))
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, is_active);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);")
        logger.info("✅ БД инициализирована.")

    async def get_user(self, tg_id: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
            if not row:
                # 🔥 Используем UPSERT: вставляем, если не существует, иначе ничего не делаем
                await conn.execute("""
                    INSERT INTO users (tg_id) VALUES ($1)
                    ON CONFLICT (tg_id) DO NOTHING
                """, tg_id)
                row = await conn.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
            return dict(row)

    async def set_consent(self, tg_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET consent_pd = TRUE WHERE tg_id = $1", tg_id)

    async def update_user(self, tg_id: int, **kwargs):
        async with self.pool.acquire() as conn:
            for key, value in kwargs.items():
                if key == 'tg_id': continue
                await conn.execute(f"UPDATE users SET {key} = $1 WHERE tg_id = $2", value, tg_id)

    async def set_grade_range(self, tg_id: int, grade_range: str):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET grade_range = $1 WHERE tg_id = $2", grade_range, tg_id)

    async def update_memory(self, tg_id: int, notes: str):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET memory_notes = $1 WHERE tg_id = $2", notes, tg_id)

    async def set_voice_enabled(self, tg_id: int, enabled: bool):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET voice_enabled = $1 WHERE tg_id = $2", enabled, tg_id)

    async def set_last_quiz_topic(self, tg_id: int, topic: str):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET last_quiz_topic = $1 WHERE tg_id = $2", topic, tg_id)

    async def decrement_free_request(self, tg_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET free_requests = free_requests - 1 WHERE tg_id = $1", tg_id)

    async def record_request(self, tg_id: int):
        await self.record_activity(tg_id)
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET total_requests = COALESCE(total_requests, 0) + 1 WHERE tg_id = $1", tg_id)
            await conn.execute(
                "INSERT INTO user_events (user_id, event_type) VALUES ($1, 'request')",
                tg_id,
            )

    def _estimate_memory_importance(self, role: str, content: str) -> int:
        text = (content or "").lower()
        high_value_markers = [
            "ошиб", "не понял", "не понимаю", "проверь себя", "ответ", "задач",
            "егэ", "огэ", "тема", "формул", "реш", "объясни", "запомни",
        ]
        if any(marker in text for marker in high_value_markers):
            return 3
        if role == "assistant" and len(text) > 600:
            return 2
        return 1

    def _extract_memory_tags(self, content: str) -> str:
        text = (content or "").lower()
        tags = []
        tag_markers = {
            "math": ["матем", "уравнен", "функц", "производн", "интеграл", "геометр"],
            "russian": ["русск", "сочинен", "орфограф", "пунктуац"],
            "physics": ["физик", "сила", "скорост", "ток", "напряж"],
            "chemistry": ["хими", "реакц", "молекул"],
            "exam": ["егэ", "огэ", "экзамен"],
            "self_check": ["проверь себя"],
            "mistake": ["ошиб", "неправильно"],
        }
        for tag, markers in tag_markers.items():
            if any(marker in text for marker in markers):
                tags.append(tag)
        return ",".join(tags)

    async def add_dialog_message(self, tg_id: int, role: str, content: str):
        content = (content or "").strip()
        if not content:
            return
        importance = self._estimate_memory_importance(role, content)
        tags = self._extract_memory_tags(content)
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ai_dialog_messages (user_id, role, content, importance, tags)
                VALUES ($1, $2, $3, $4, $5)
            """, tg_id, role, content[:4000], importance, tags)
            await conn.execute("""
                DELETE FROM ai_dialog_messages
                WHERE id IN (
                    SELECT id
                    FROM ai_dialog_messages
                    WHERE user_id = $1
                    ORDER BY created_at DESC, id DESC
                    OFFSET 80
                )
            """, tg_id)

    async def get_dialog_context(self, tg_id: int, limit: int = 8) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content
                FROM ai_dialog_messages
                WHERE user_id = $1
                ORDER BY created_at DESC, id DESC
                LIMIT $2
            """, tg_id, limit)
        return [
            {"role": row["role"], "content": row["content"]}
            for row in reversed(rows)
        ]

    async def search_dialog_memory(self, tg_id: int, query: str, limit: int = 4) -> list[dict]:
        query = (query or "").strip()
        if len(query) < 3:
            return []
        keywords = [
            word for word in re.findall(r"[A-Za-zА-Яа-яЁё0-9]{4,}", query.lower())
            if word not in {"который", "которая", "почему", "объясни", "задача", "ответ"}
        ][:5]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content, created_at, importance, tags
                FROM ai_dialog_messages
                WHERE user_id = $1
                  AND id NOT IN (
                      SELECT id
                      FROM ai_dialog_messages
                      WHERE user_id = $1
                      ORDER BY created_at DESC, id DESC
                      LIMIT 8
                  )
                  AND (
                      to_tsvector('simple', content) @@ plainto_tsquery('simple', $2)
                      OR content ILIKE '%' || $2 || '%'
                  )
                ORDER BY importance DESC, created_at DESC
                LIMIT $3
            """, tg_id, query[:300], limit)
            if len(rows) < limit and keywords:
                conditions = " OR ".join(f"LOWER(content) LIKE ${idx + 3}" for idx in range(len(keywords)))
                more_rows = await conn.fetch(f"""
                    SELECT role, content, created_at, importance, tags
                    FROM ai_dialog_messages
                    WHERE user_id = $1
                      AND id NOT IN (
                          SELECT id
                          FROM ai_dialog_messages
                          WHERE user_id = $1
                          ORDER BY created_at DESC, id DESC
                          LIMIT 8
                      )
                      AND ({conditions})
                    ORDER BY importance DESC, created_at DESC
                    LIMIT $2
                """, tg_id, limit - len(rows), *[f"%{word}%" for word in keywords])
                rows = list(rows) + list(more_rows)
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "importance": row["importance"],
                "tags": row["tags"] or "",
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    async def get_memory_profile(self, tg_id: int) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT summary, learning_profile, last_message_id, updated_at
                FROM ai_memory_profiles
                WHERE user_id = $1
            """, tg_id)
        if not row:
            return {"summary": "", "learning_profile": "", "last_message_id": 0, "updated_at": None}
        return {
            "summary": row["summary"] or "",
            "learning_profile": row["learning_profile"] or "",
            "last_message_id": row["last_message_id"] or 0,
            "updated_at": row["updated_at"],
        }

    async def update_memory_profile(self, tg_id: int, summary: str, learning_profile: str = "", last_message_id: int = 0):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO ai_memory_profiles (user_id, summary, learning_profile, last_message_id, updated_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    summary = EXCLUDED.summary,
                    learning_profile = EXCLUDED.learning_profile,
                    last_message_id = EXCLUDED.last_message_id,
                    updated_at = NOW()
            """, tg_id, summary[:3000], learning_profile[:1500], last_message_id)

    async def get_latest_dialog_message_id(self, tg_id: int) -> int:
        async with self.pool.acquire() as conn:
            value = await conn.fetchval("""
                SELECT COALESCE(MAX(id), 0)
                FROM ai_dialog_messages
                WHERE user_id = $1
            """, tg_id)
        return value or 0

    async def get_recent_dialog_text(self, tg_id: int, limit: int = 20) -> str:
        rows = await self.get_dialog_context(tg_id, limit=limit)
        return "\n".join(
            f"{item['role']}: {item['content'][:1200]}"
            for item in rows
        )

    async def clear_dialog_context(self, tg_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM ai_dialog_messages WHERE user_id = $1", tg_id)
            await conn.execute("DELETE FROM ai_memory_profiles WHERE user_id = $1", tg_id)

    async def record_activity(self, tg_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_sessions
                SET is_active = FALSE,
                    duration_seconds = GREATEST(0, EXTRACT(EPOCH FROM (last_activity - started_at))::INT)
                WHERE user_id = $1
                  AND is_active = TRUE
                  AND last_activity < NOW() - INTERVAL '30 minutes'
            """, tg_id)
            await self.refresh_time_stats(tg_id, conn=conn)

            session = await conn.fetchrow("""
                SELECT id
                FROM user_sessions
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY started_at DESC
                LIMIT 1
            """, tg_id)

            if session:
                await conn.execute("""
                    UPDATE user_sessions
                    SET last_activity = NOW()
                    WHERE id = $1
                """, session["id"])
            else:
                await conn.execute("""
                    INSERT INTO user_sessions (user_id)
                    VALUES ($1)
                """, tg_id)

    async def cleanup_old_sessions(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_sessions
                SET is_active = FALSE,
                    duration_seconds = GREATEST(0, EXTRACT(EPOCH FROM (last_activity - started_at))::INT)
                WHERE is_active = TRUE
                  AND last_activity < NOW() - INTERVAL '1 hour'
            """)
            await self.refresh_time_stats(conn=conn)

    async def refresh_time_stats(self, tg_id: int | None = None, conn=None):
        own_conn = conn is None
        if own_conn:
            conn = await self.pool.acquire()
        try:
            where_clause = "WHERE user_id = $1" if tg_id is not None else ""
            params = [tg_id] if tg_id is not None else []
            rows = await conn.fetch(f"""
                SELECT
                    user_id,
                    COALESCE(SUM(duration_seconds), 0)::BIGINT as total_seconds,
                    COUNT(*)::INT as session_count,
                    COALESCE(MAX(duration_seconds), 0)::INT as longest_session_seconds
                FROM user_sessions
                {where_clause}
                AND is_active = FALSE
                GROUP BY user_id
            """ if tg_id is not None else """
                SELECT
                    user_id,
                    COALESCE(SUM(duration_seconds), 0)::BIGINT as total_seconds,
                    COUNT(*)::INT as session_count,
                    COALESCE(MAX(duration_seconds), 0)::INT as longest_session_seconds
                FROM user_sessions
                WHERE is_active = FALSE
                GROUP BY user_id
            """, *params)
            for row in rows:
                await conn.execute("""
                    INSERT INTO user_time_stats (user_id, total_seconds, session_count, longest_session_seconds, updated_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    ON CONFLICT (user_id) DO UPDATE SET
                        total_seconds = EXCLUDED.total_seconds,
                        session_count = EXCLUDED.session_count,
                        longest_session_seconds = EXCLUDED.longest_session_seconds,
                        updated_at = NOW()
                """, row["user_id"], row["total_seconds"], row["session_count"], row["longest_session_seconds"])
        finally:
            if own_conn:
                await self.pool.release(conn)

    async def get_activity_stats(self, tg_id: int) -> dict:
        await self.cleanup_old_sessions()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT total_seconds, session_count, longest_session_seconds
                FROM user_time_stats
                WHERE user_id = $1
            """, tg_id)
            active = await conn.fetchrow("""
                SELECT started_at, last_activity
                FROM user_sessions
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY started_at DESC
                LIMIT 1
            """, tg_id)
            today = await conn.fetchval("""
                SELECT COALESCE(SUM(duration_seconds), 0)::BIGINT
                FROM user_sessions
                WHERE user_id = $1
                  AND is_active = FALSE
                  AND started_at::date = CURRENT_DATE
            """, tg_id)

        total_seconds = (row["total_seconds"] if row else 0) or 0
        active_seconds = 0
        if active:
            active_seconds = max(0, int((active["last_activity"] - active["started_at"]).total_seconds()))

        return {
            "total_seconds": total_seconds + active_seconds,
            "completed_seconds": total_seconds,
            "active_seconds": active_seconds,
            "today_seconds": (today or 0) + active_seconds,
            "session_count": (row["session_count"] if row else 0) or 0,
            "longest_session_seconds": (row["longest_session_seconds"] if row else 0) or 0,
            "has_active_session": bool(active),
        }

    async def activate_subscription(self, tg_id: int, mode: str, days: int = 30):
        expires = datetime.now() + timedelta(days=days)
        async with self.pool.acquire() as conn:
            await conn.execute(f"UPDATE users SET {mode}_sub = TRUE, {mode}_expires = $1 WHERE tg_id = $2", expires, tg_id)
