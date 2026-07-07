"""Production baseline Tutor-RAG pipeline.

The pipeline keeps retrieval deterministic and explainable:
- infer subject/task metadata from the student query;
- retrieve candidates from PostgreSQL;
- rerank tasks locally;
- return compact context only when confidence is useful.
"""
from dataclasses import dataclass
import re

from ..core.config import env_float, env_int
from .search import normalize_tokens


SUBJECT_ALIASES = {
    "math": {
        "математика", "матеша", "алгебра", "геометрия", "пифагор",
        "производная", "интеграл", "функция", "уравнение",
    },
    "russian": {"русский", "орфография", "пунктуация", "сочинение", "текст"},
    "physics": {"физика", "ток", "напряжение", "сила", "скорость", "энергия"},
    "chemistry": {"химия", "реакция", "моль", "вещество", "кислота"},
    "biology": {"биология", "клетка", "ген", "организм", "растение"},
    "informatics": {"информатика", "python", "алгоритм", "код", "программа"},
    "english": {"английский", "english", "grammar", "vocabulary"},
    "social-studies": {"обществознание", "право", "экономика", "общество"},
}

TASK_NUMBER_RE = re.compile(
    r"(?:задани[ея]|номер|№|no\.?|task)\s*([0-9]{1,2})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RagQuery:
    raw: str
    tokens: list[str]
    subject_code: str | None = None
    task_number: int | None = None


@dataclass(frozen=True)
class RagResult:
    text: str
    used: bool
    confidence: float
    tasks: list[dict]
    query: RagQuery


def analyze_query(text: str) -> RagQuery:
    raw = (text or "").strip()
    normalized = raw.lower().replace("ё", "е")
    tokens = normalize_tokens(normalized, limit=12)
    token_set = set(tokens)

    subject_code = None
    best_matches = 0
    for code, aliases in SUBJECT_ALIASES.items():
        aliases_normalized = {alias.replace("ё", "е") for alias in aliases}
        matches = sum(
            1
            for token in token_set
            for alias in aliases_normalized
            if token == alias
            or token in alias
            or alias in token
            or (len(token) >= 6 and len(alias) >= 6 and token[:6] == alias[:6])
        )
        if matches > best_matches:
            subject_code = code
            best_matches = matches

    task_number = None
    number_match = TASK_NUMBER_RE.search(normalized)
    if number_match:
        try:
            task_number = int(number_match.group(1))
        except ValueError:
            task_number = None

    return RagQuery(
        raw=raw,
        tokens=tokens,
        subject_code=subject_code,
        task_number=task_number,
    )


def _confidence_from_tasks(tasks: list[dict]) -> float:
    if not tasks:
        return 0.0
    top_score = float(tasks[0].get("rag_score") or 0.0)
    if top_score <= 0:
        return 0.0
    support_bonus = min(0.2, 0.04 * max(0, len(tasks) - 1))
    return min(1.0, (top_score / 12.0) + support_bonus)


def _format_task(task: dict, index: int) -> str:
    topic = task.get("topic") or "тема не указана"
    subject = task.get("subject_name") or task.get("subject_code") or "предмет"
    number = task.get("task_number") or "?"
    condition = (task.get("condition") or "").strip()
    solution = (task.get("solution") or "").strip()
    answer = (task.get("answer") or "").strip()

    parts = [
        f"Пример {index}: {subject}, задание {number}, тема: {topic}",
        f"Условие: {condition[:900]}",
    ]
    if solution:
        parts.append(f"Решение из базы: {solution[:700]}")
    if answer:
        parts.append(f"Ответ из базы: {answer[:160]}")
    return "\n".join(parts)


async def build_tutor_rag_context(task_search, user_text: str) -> RagResult:
    query = analyze_query(user_text)
    if not task_search or (not query.tokens and query.task_number is None and not query.subject_code):
        return RagResult("", False, 0.0, [], query)

    limit = env_int("RAG_CONTEXT_TASK_LIMIT", 3, minimum=1)
    min_confidence = env_float("RAG_MIN_CONFIDENCE", 0.22, minimum=0.0)
    candidates = await task_search.search_ranked_tasks(
        query.raw,
        subject_code=query.subject_code,
        task_number=query.task_number,
        limit=max(limit, 5),
    )

    if not candidates and query.subject_code:
        candidates = await task_search.search_ranked_tasks(
            query.raw,
            subject_code=None,
            task_number=query.task_number,
            limit=max(limit, 5),
        )

    confidence = _confidence_from_tasks(candidates)
    if confidence < min_confidence:
        return RagResult("", False, confidence, candidates[:limit], query)

    selected = candidates[:limit]
    context = "\n\n".join(_format_task(task, index + 1) for index, task in enumerate(selected))
    metadata = []
    if query.subject_code:
        metadata.append(f"предмет={query.subject_code}")
    if query.task_number is not None:
        metadata.append(f"номер_задания={query.task_number}")
    if query.tokens:
        metadata.append("ключевые_слова=" + ", ".join(query.tokens[:8]))

    text = (
        "Контекст из базы задач. Используй его только как опору, если он действительно подходит запросу. "
        "Не выдавай решение из базы как единственно возможное, а объясняй ученику по шагам.\n"
        f"Уверенность RAG: {confidence:.2f}"
    )
    if metadata:
        text += "\n" + "; ".join(metadata)
    text += "\n\n" + context
    return RagResult(text, True, confidence, selected, query)
