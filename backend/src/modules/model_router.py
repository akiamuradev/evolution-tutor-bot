"""Model routing for OpenRouter requests."""
import logging
import os
import re

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-72b-instruct")
FAST_MODEL = os.getenv("OPENROUTER_FAST_MODEL", DEFAULT_OPENROUTER_MODEL)
REASONING_MODEL = os.getenv("OPENROUTER_REASONING_MODEL", "deepseek/deepseek-r1")
FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "google/gemini-2.5-pro")
BUSINESS_MODEL = os.getenv("OPENROUTER_BUSINESS_MODEL", DEFAULT_OPENROUTER_MODEL)

MODE_MODELS = {
    "fast": FAST_MODEL,
    "standard": DEFAULT_OPENROUTER_MODEL,
    "schoolboy": DEFAULT_OPENROUTER_MODEL,
    "reasoning": REASONING_MODEL,
    "fallback": FALLBACK_MODEL,
    "business": BUSINESS_MODEL,
}

FAST_MARKERS = (
    "привет", "спасибо", "кнопк", "меню", "профиль", "статистик", "достижен",
    "что ты умеешь", "как пользоваться", "покажи", "объясни коротко",
)

REASONING_MARKERS = (
    "егэ", "огэ", "впр", "параметр", "докажи", "доказать", "геометр",
    "стереометр", "планиметр", "тригонометр", "логарифм", "производн",
    "интеграл", "вероятност", "комбинатор", "физик", "информат",
    "алгоритм", "график функции", "система уравнений", "неравенств",
    "текстовая задача", "олимпиад",
)

SCHOOL_SUBJECT_MARKERS = (
    "математ", "русский", "литератур", "истори", "обществ", "биолог",
    "хими", "физик", "информат", "английск", "географ", "задач",
    "пример", "уравнен", "катет", "гипотенуз", "процент", "дроб",
)


def _normalize(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def classify_question_complexity(question: str) -> str:
    """Return fast, standard, or reasoning."""
    text = _normalize(question)
    numbers = re.findall(r"\d+", text)
    has_formula = bool(re.search(r"[=+\-*/^√]|[a-zа-я]\s*\^?\s*2", text))
    has_reasoning_marker = any(marker in text for marker in REASONING_MARKERS)
    has_school_marker = any(marker in text for marker in SCHOOL_SUBJECT_MARKERS)

    if has_reasoning_marker:
        return "reasoning"
    if len(text) > 1200 or (len(numbers) >= 4 and has_school_marker):
        return "reasoning"
    if has_formula and has_school_marker:
        return "reasoning"
    if len(text) <= 120 and any(marker in text for marker in FAST_MARKERS):
        return "fast"
    return "standard"


def select_model(mode: str = "standard", question: str = "") -> str:
    """Select an OpenRouter model for the current task."""
    normalized_mode = (mode or "standard").lower()
    if normalized_mode in {"fast", "reasoning", "fallback", "business"}:
        model = MODE_MODELS[normalized_mode]
        complexity = normalized_mode
    else:
        complexity = classify_question_complexity(question)
        model = MODE_MODELS.get(complexity, DEFAULT_OPENROUTER_MODEL)

    logger.info("OpenRouter model selected: mode=%s complexity=%s model=%s", mode, complexity, model)
    return model


def get_fallback_models(primary_model: str) -> list[str]:
    """Return unique fallback candidates after the primary model."""
    candidates = [
        FALLBACK_MODEL,
        DEFAULT_OPENROUTER_MODEL,
        REASONING_MODEL,
        FAST_MODEL,
    ]
    result = []
    for candidate in candidates:
        if candidate and candidate != primary_model and candidate not in result:
            result.append(candidate)
    return result


def get_timeout_for_complexity(complexity: str = "standard") -> int:
    if complexity == "fast":
        return int(os.getenv("OPENROUTER_FAST_TIMEOUT", "60"))
    if complexity == "reasoning":
        return int(os.getenv("OPENROUTER_REASONING_TIMEOUT", "180"))
    return int(os.getenv("OPENROUTER_TIMEOUT", "120"))


def get_max_tokens_for_complexity(complexity: str = "standard") -> int:
    if complexity == "fast":
        return int(os.getenv("OPENROUTER_FAST_MAX_TOKENS", "900"))
    if complexity == "reasoning":
        return int(os.getenv("OPENROUTER_REASONING_MAX_TOKENS", "2500"))
    return int(os.getenv("OPENROUTER_MAX_TOKENS", "1800"))
