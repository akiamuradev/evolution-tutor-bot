"""Intent helpers for tutor response policy.

The tutor should guide concrete task solving, but explain concepts directly.
"""
import re


def normalize_text(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def wants_full_answer(user_text: str) -> bool:
    text = normalize_text(user_text)
    return any(marker in text for marker in (
        "покажи ответ",
        "дай ответ",
        "готовый ответ",
        "полное решение",
        "реши полностью",
        "сразу ответ",
    ))


def is_conceptual_question(user_text: str) -> bool:
    text = normalize_text(user_text)
    return any(marker in text for marker in (
        "что такое",
        "это?",
        "как работает",
        "почему",
        "зачем",
        "объясни",
        "расскажи",
        "что произойдет",
        "что будет если",
        "можно ли",
        "смогу ли",
        "как устроен",
        "как устроена",
        "как устроено",
        "чем отличается",
    ))


def _looks_like_answer_attempt(user_text: str) -> bool:
    text = normalize_text(user_text)
    numbers = re.findall(r"\d+", text)
    if not numbers:
        return False

    answer_markers = (
        "получилось",
        "получится",
        "ответ",
        "равно",
        "будет",
        "значит",
        "думаю",
    )
    math_symbols = ("=", "+", "-", "*", "/", "²", "^", "√")
    is_short = len(text) <= 120
    return (
        any(marker in text for marker in answer_markers)
        or any(symbol in text for symbol in math_symbols)
        or is_short
    )


def should_force_guided_mode(user_text: str, history: list[dict]) -> bool:
    if wants_full_answer(user_text):
        return False

    text = normalize_text(user_text)
    previous_text = normalize_text("\n".join(item["content"][-800:] for item in history[-4:]))
    numbers = re.findall(r"\d+", text)

    solve_markers = (
        "реши", "решить", "посчитай", "сосчитай", "вычисли", "рассчитай",
        "найди", "определи", "сколько будет", "сколько равн", "получится",
        "разбери", "помоги с", "как решить", "как найти", "что выйдет",
    )
    task_markers = (
        "катет", "гипотенуз", "уравнен", "задач", "пример", "см", "метр",
        "треугольник", "периметр", "площад", "процент", "корень", "степен",
        "дроб", "функц", "график", "угол", "радиус", "диаметр", "скорост",
    )
    math_symbols = ("=", "+", "-", "*", "/", "²", "^", "√")

    follows_self_check = "проверь себя" in previous_text
    has_solve_intent = any(marker in text for marker in solve_markers)
    has_task_signal = any(marker in text for marker in task_markers) or any(symbol in text for symbol in math_symbols)
    has_enough_task_data = len(numbers) >= 2 and has_task_signal
    concept_question = is_conceptual_question(user_text)
    answer_attempt = _looks_like_answer_attempt(user_text)

    if concept_question and not (has_solve_intent and has_enough_task_data):
        return False

    return (
        (follows_self_check and answer_attempt)
        or (has_solve_intent and has_task_signal)
        or has_enough_task_data
    )


def build_guided_task_response(user_text: str) -> str:
    text = normalize_text(user_text)
    numbers = [int(item) for item in re.findall(r"\d+", text)]

    if ("катет" in text or "гипотенуз" in text or "треугольник" in text) and len(numbers) >= 2:
        a, b = numbers[0], numbers[1]
        return (
            "Давай разберем как на тренировке: я не дам готовое число сразу, "
            "а помогу тебе самому до него дойти.\n\n"
            "Что мы ищем:\n"
            "Гипотенуза - это самая длинная сторона прямоугольного треугольника. "
            "Она лежит напротив прямого угла.\n\n"
            "Какая идея:\n"
            "Если известны два катета, используем теорему Пифагора:\n"
            "c² = a² + b²\n\n"
            "Это значит: сначала мы находим квадрат гипотенузы, а уже потом извлекаем корень.\n\n"
            f"Подставим твои катеты: {a} см и {b} см.\n\n"
            "Первый шаг - возвести катеты в квадрат:\n"
            f"{a}² = {a * a}\n"
            f"{b}² = {b * b}\n\n"
            "Почему именно так:\n"
            "Мы не складываем сами стороны, потому что теорема работает с квадратами сторон.\n\n"
            f"Теперь твой ход: сложи {a * a} + {b * b}. Это будет c².\n"
            "Напиши, что получилось, и я проверю следующий шаг."
        )

    if "уравнен" in text:
        return (
            "Давай не буду сразу выдавать ответ, а помогу решить.\n\n"
            "Первый шаг: перепиши уравнение и выдели, где неизвестное число. "
            "Потом попробуй перенести известные числа в другую сторону.\n\n"
            "Пришли свой первый шаг, и я проверю."
        )

    return (
        "Давай сделаем это по шагам, чтобы ты сам дошел до ответа.\n\n"
        "Сначала выпиши, что дано в задаче и какую формулу или правило можно применить. "
        "Пришли этот первый шаг, а я проверю и помогу дальше."
    )


def build_tutor_policy_context(user_text: str, history: list[dict]) -> str:
    if not should_force_guided_mode(user_text, history):
        return ""
    return (
        "Учебный режим для текущего сообщения:\n"
        "- Это похоже на задачу или проверку ответа ученика.\n"
        "- Не выдавай финальный числовой ответ сразу, даже если ученик просит решить.\n"
        "- Сначала объясни идею, формулу и сделай один небольшой шаг.\n"
        "- Попроси ученика выполнить следующий шаг самостоятельно.\n"
        "- Если ученик уже прислал попытку ответа, проверь ее и объясни ошибку."
    )
