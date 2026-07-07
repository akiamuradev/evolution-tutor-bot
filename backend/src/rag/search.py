"""Task search helpers used by practice and Tutor-RAG."""
import re
from typing import Dict, List, Optional


TOKEN_RE = re.compile(r"[^\W_]{3,}", re.UNICODE)
STOP_WORDS = {
    "как", "что", "это", "для", "или", "при", "над", "под", "без", "про",
    "мне", "мой", "моя", "мои", "твой", "тебе", "тебя", "реши", "решить",
    "объясни", "объяснить", "задача", "задание", "ответ", "найди", "почему",
    "будет", "если", "нужно", "можно", "через", "дано", "где", "когда",
}


def normalize_tokens(text: str, limit: int = 10) -> list[str]:
    tokens = []
    seen = set()
    for raw_token in TOKEN_RE.findall((text or "").lower()):
        token = raw_token.replace("ё", "е")
        if token in STOP_WORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
        if len(tokens) >= limit:
            break
    return tokens


class TaskSearch:
    """Поиск задач в PostgreSQL"""
    
    def __init__(self, pool):
        self.pool = pool
    
    async def get_random_tasks(
        self,
        subject_code: Optional[str] = None,
        count: int = 5,
        difficulty: Optional[str] = None
    ) -> List[Dict]:
        """Получает случайные задачи для тренировки. Если subject_code=None — из всех предметов"""
        async with self.pool.acquire() as conn:
            sql = """
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.condition, t.solution, t.answer,
                    s.name as subject_name, s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE 1=1
            """
            params = []
            param_idx = 1
            
            if subject_code:
                sql += f" AND s.code = ${param_idx}"
                params.append(subject_code)
                param_idx += 1
            
            if difficulty:
                sql += f" AND t.difficulty = ${param_idx}"
                params.append(difficulty)
                param_idx += 1
            
            sql += f" ORDER BY RANDOM() LIMIT {count}"
            
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def get_tasks_by_topic(
        self,
        topic: str,
        subject_code: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Получает задачи по теме"""
        async with self.pool.acquire() as conn:
            sql = """
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.subtopic, t.condition, t.solution, t.answer,
                    s.name as subject_name, s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.topic ILIKE $1
            """
            params = [f"%{topic}%"]
            param_idx = 2
            
            if subject_code:
                sql += f" AND s.code = ${param_idx}"
                params.append(subject_code)
                param_idx += 1
            
            sql += f" ORDER BY RANDOM() LIMIT {limit}"
            
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def search_tasks(
        self,
        query: str,
        subject_code: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Поиск задач по тексту условия"""
        async with self.pool.acquire() as conn:
            sql = """
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.condition, t.solution, t.answer,
                    s.name as subject_name, s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.condition ILIKE $1
            """
            params = [f"%{query}%"]
            param_idx = 2
            
            if subject_code:
                sql += f" AND s.code = ${param_idx}"
                params.append(subject_code)
                param_idx += 1
            
            sql += f" ORDER BY RANDOM() LIMIT {limit}"
            
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def search_by_keywords(
        self,
        keywords: str,
        subject_code: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Поиск задач по ключевым словам в условии и теме"""
        async with self.pool.acquire() as conn:
            sql = """
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.subtopic, t.condition, t.solution, t.answer,
                    s.name as subject_name, s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.condition ILIKE $1 OR t.topic ILIKE $1
            """
            params = [f"%{keywords}%"]
            param_idx = 2
            
            if subject_code:
                sql += f" AND s.code = ${param_idx}"
                params.append(subject_code)
                param_idx += 1
            
            sql += f" ORDER BY RANDOM() LIMIT {limit}"
            
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]

    async def search_ranked_tasks(
        self,
        query: str,
        subject_code: Optional[str] = None,
        task_number: Optional[int] = None,
        limit: int = 5,
        fetch_limit: int = 80,
    ) -> List[Dict]:
        """Search tasks with metadata filters and local reranking.

        This is intentionally database-light: it works on the current schema,
        uses indexes where possible, and keeps reranking in Python until we add
        proper vector search.
        """
        tokens = normalize_tokens(query)
        if not tokens and task_number is None and not subject_code:
            return []

        async with self.pool.acquire() as conn:
            params = []
            conditions = []
            param_idx = 1

            if subject_code:
                conditions.append(f"s.code = ${param_idx}")
                params.append(subject_code)
                param_idx += 1

            if task_number is not None:
                conditions.append(f"t.task_number = ${param_idx}")
                params.append(task_number)
                param_idx += 1

            if tokens:
                token_clauses = []
                for token in tokens:
                    token_clauses.append(
                        "("
                        f"LOWER(COALESCE(t.condition, '')) LIKE ${param_idx} OR "
                        f"LOWER(COALESCE(t.topic, '')) LIKE ${param_idx} OR "
                        f"LOWER(COALESCE(t.subtopic, '')) LIKE ${param_idx} OR "
                        f"LOWER(COALESCE(t.answer, '')) LIKE ${param_idx}"
                        ")"
                    )
                    params.append(f"%{token}%")
                    param_idx += 1
                conditions.append("(" + " OR ".join(token_clauses) + ")")

            where_clause = " AND ".join(conditions) if conditions else "TRUE"
            sql = f"""
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.subtopic, t.condition, t.solution, t.answer,
                    t.source_url,
                    s.name as subject_name, s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE {where_clause}
                LIMIT {max(limit, fetch_limit)}
            """
            rows = await conn.fetch(sql, *params)

        ranked = []
        for row in rows:
            task = dict(row)
            score = self._score_task(task, query, tokens, subject_code, task_number)
            if score > 0:
                task["rag_score"] = score
                ranked.append(task)

        ranked.sort(key=lambda item: item["rag_score"], reverse=True)
        return ranked[:limit]

    def _score_task(
        self,
        task: Dict,
        query: str,
        tokens: list[str],
        subject_code: Optional[str],
        task_number: Optional[int],
    ) -> float:
        topic = (task.get("topic") or "").lower().replace("ё", "е")
        subtopic = (task.get("subtopic") or "").lower().replace("ё", "е")
        condition = (task.get("condition") or "").lower().replace("ё", "е")
        answer = (task.get("answer") or "").lower().replace("ё", "е")
        source = f"{topic} {subtopic} {condition} {answer}"

        score = 0.0
        if subject_code and task.get("subject_code") == subject_code:
            score += 0.8
        if task_number is not None and task.get("task_number") == task_number:
            score += 4.0

        query_text = (query or "").lower().replace("ё", "е").strip()
        if query_text and query_text in source:
            score += 4.0

        for token in tokens:
            if token in topic:
                score += 3.0
            elif token in subtopic:
                score += 2.5
            elif token in condition:
                score += 1.2
            elif token in answer:
                score += 0.4

        if task.get("solution"):
            score += 0.5
        if task.get("answer"):
            score += 0.25
        return score
