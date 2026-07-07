"""HTTP API route handlers."""
import logging
import re

from aiohttp import web

from ..core.config import env_bool, env_int, env_str
from ..helpers import get_user_grade
from ..modules.anti_spam import anti_spam_guard
from ..modules.ai_gateway import ai_gateway_stats
from ..modules.generation_control import generation_registry
from ..modules.request_guard import ai_request_guard
from ..modules.tutor_engine import generate_tutor_response
from ..routers.achievements import (
    ACHIEVEMENTS,
    RARITY_LABELS,
    achievement_progress,
    check_achievements,
    get_unlocked_achievement_ids,
    get_user_achievement_stats,
)
from ..services import db, services
from .auth import get_authenticated_user_id
from .utils import error_response, json_response

logger = logging.getLogger(__name__)
PRACTICE_SUBJECTS = {
    "math",
    "russian",
    "physics",
    "chemistry",
    "biology",
    "social-studies",
    "informatics",
    "english",
}


async def handle_options(_: web.Request) -> web.Response:
    return json_response({"ok": True})


async def handle_health(_: web.Request) -> web.Response:
    return json_response({
        "ok": True,
        "service": "tutor-api",
        "anti_spam": anti_spam_guard.stats(),
        "ai_queue": ai_request_guard.stats(),
        "ai_gateway": ai_gateway_stats.stats(),
        "generations": generation_registry.stats(),
        "db": bool(db.pool),
        "rag": bool(services.task_search),
        "vk_auth_configured": bool(env_str("VK_APP_SECRET")),
        "unsigned_vk_launch_allowed": env_bool("WEB_API_ALLOW_UNSIGNED_VK_LAUNCH", False),
        "dev_user_id_allowed": env_bool("WEB_API_ALLOW_INSECURE_USER_ID", False),
    })


def _auth_payload_from_request(request: web.Request) -> dict:
    return {
        "launch_params": request.query.get("launch_params", ""),
        "user_id": request.query.get("user_id"),
    }


def _format_seconds(seconds: int) -> str:
    seconds = max(0, int(seconds or 0))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def _normalize_answer(answer: str) -> str:
    return re.sub(r"\s+", "", str(answer or "").lower().replace("ё", "е"))


def _task_public_payload(task: dict) -> dict:
    return {
        "id": task.get("id"),
        "year": task.get("year"),
        "task_number": task.get("task_number"),
        "difficulty": task.get("difficulty"),
        "topic": task.get("topic"),
        "subtopic": task.get("subtopic"),
        "condition": task.get("condition"),
        "subject_name": task.get("subject_name"),
        "subject_code": task.get("subject_code"),
        "has_answer": bool(task.get("answer")),
        "has_solution": bool(task.get("solution")),
    }


async def _get_authenticated_request_user(request: web.Request) -> tuple[int | None, str]:
    return get_authenticated_user_id(_auth_payload_from_request(request))


async def handle_profile(request: web.Request) -> web.Response:
    user_id, auth_source = await _get_authenticated_request_user(request)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    user = await db.get_user(user_id)
    activity = await db.get_activity_stats(user_id)
    unlocked_ids = await get_unlocked_achievement_ids(user_id)

    subscription = "free"
    if user.get("business_sub"):
        subscription = "business"
    elif user.get("standard_sub"):
        subscription = "standard"
    elif user.get("student_sub"):
        subscription = "student"

    return json_response({
        "ok": True,
        "profile": {
            "user_id": user_id,
            "grade": get_user_grade(user),
            "total_requests": user.get("total_requests") or 0,
            "free_requests": user.get("free_requests") or 0,
            "subscription": subscription,
            "achievements_unlocked": len(unlocked_ids),
            "activity": activity,
        },
        "auth_source": auth_source,
    })


async def handle_achievements(request: web.Request) -> web.Response:
    user_id, auth_source = await _get_authenticated_request_user(request)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    await check_achievements(user_id)
    stats = await get_user_achievement_stats(user_id)
    unlocked_ids = await get_unlocked_achievement_ids(user_id)

    items = []
    for achievement in ACHIEVEMENTS:
        current, target = achievement_progress(achievement, stats)
        unlocked = achievement.id in unlocked_ids
        items.append({
            "id": achievement.id,
            "emoji": achievement.emoji,
            "title": achievement.name if unlocked else achievement.name,
            "condition": achievement.condition,
            "description": achievement.description if unlocked else achievement.condition,
            "rarity": achievement.rarity,
            "rarity_label": RARITY_LABELS.get(achievement.rarity, achievement.rarity),
            "unlocked": unlocked,
            "current": current,
            "target": target,
            "progress": int(current / target * 100) if target else 0,
        })

    unlocked_count = len(unlocked_ids)
    total_count = len(ACHIEVEMENTS)
    return json_response({
        "ok": True,
        "summary": {
            "unlocked": unlocked_count,
            "total": total_count,
            "percent": int(unlocked_count / total_count * 100) if total_count else 0,
        },
        "achievements": items,
        "auth_source": auth_source,
    })


async def handle_activity(request: web.Request) -> web.Response:
    user_id, auth_source = await _get_authenticated_request_user(request)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    await db.record_activity(user_id)
    stats = await db.get_activity_stats(user_id)
    return json_response({
        "ok": True,
        "activity": {
            **stats,
            "total_text": _format_seconds(stats["total_seconds"]),
            "today_text": _format_seconds(stats["today_seconds"]),
            "active_text": _format_seconds(stats["active_seconds"]),
            "longest_text": _format_seconds(stats["longest_session_seconds"]),
        },
        "auth_source": auth_source,
    })


async def _check_api_action(user_id: int, action: str) -> web.Response | None:
    decision = anti_spam_guard.check_user(user_id, action=action)
    if not decision.allowed:
        return error_response(
            "rate_limited",
            status=429,
            reason=decision.reason,
            retry_after=decision.retry_after or 3,
        )

    acquired = await anti_spam_guard.acquire_global(action=action)
    if not acquired:
        return error_response("busy", status=503, retry_after=5)
    return None


async def handle_practice_task(request: web.Request) -> web.Response:
    user_id, auth_source = await _get_authenticated_request_user(request)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    block_response = await _check_api_action(user_id, "api_practice")
    if block_response:
        return block_response

    try:
        if not services.task_search:
            return error_response("practice_unavailable", status=503)

        subject = (request.query.get("subject") or "").strip() or None
        if subject and subject not in PRACTICE_SUBJECTS:
            return error_response("invalid_subject")

        tasks = await services.task_search.get_random_tasks(subject, count=1)
        if not tasks:
            return error_response("task_not_found", status=404)

        await db.record_activity(user_id)
        return json_response({
            "ok": True,
            "task": _task_public_payload(tasks[0]),
            "auth_source": auth_source,
        })
    finally:
        anti_spam_guard.release_global(action="api_practice")


async def handle_practice_answer(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except Exception:
        return error_response("invalid_json")

    user_id, auth_source = get_authenticated_user_id(payload)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    block_response = await _check_api_action(user_id, "api_practice")
    if block_response:
        return block_response

    try:
        task_id = payload.get("task_id")
        user_answer = (payload.get("answer") or "").strip()
        if not task_id:
            return error_response("task_id_required")
        if not user_answer:
            return error_response("answer_required")

        async with db.pool.acquire() as conn:
            task = await conn.fetchrow("""
                SELECT
                    t.id, t.year, t.task_number, t.difficulty,
                    t.topic, t.subtopic, t.condition, t.solution, t.answer,
                    s.id as subject_id,
                    s.name as subject_name,
                    s.code as subject_code
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE t.id = $1
            """, int(task_id))

            if not task:
                return error_response("task_not_found", status=404)

            correct_answer = str(task["answer"] or "").strip()
            user_clean = _normalize_answer(user_answer)
            correct_clean = _normalize_answer(correct_answer)
            is_correct = bool(
                correct_clean
                and (
                    user_clean == correct_clean
                    or user_clean in correct_clean
                    or correct_clean in user_clean
                )
            )

            await conn.execute("""
                INSERT INTO student_progress (
                    user_id, task_id, subject_id, topic,
                    user_answer, is_correct, used_explanation
                )
                VALUES ($1, $2, $3, $4, $5, $6, FALSE)
            """, user_id, task["id"], task["subject_id"], task["topic"], user_answer, is_correct)

        await db.record_activity(user_id)
        achievements_text = await check_achievements(user_id)
        return json_response({
            "ok": True,
            "correct": is_correct,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "solution": task["solution"] or "",
            "task": _task_public_payload(dict(task)),
            "achievements_text": achievements_text or "",
            "auth_source": auth_source,
        })
    except ValueError:
        return error_response("invalid_task_id")
    finally:
        anti_spam_guard.release_global(action="api_practice")


async def handle_chat(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except Exception:
        return error_response("invalid_json")

    user_id, auth_source = get_authenticated_user_id(payload)
    if user_id is None:
        return error_response("auth_required", status=401, reason=auth_source)

    text = (payload.get("text") or "").strip()
    if not text:
        return error_response("text_required")
    if len(text) > env_int("WEB_API_MAX_TEXT_LENGTH", 4000, minimum=1):
        return error_response("text_too_long")

    decision = anti_spam_guard.check_user(user_id, action="api_chat")
    if not decision.allowed:
        return error_response(
            "rate_limited",
            status=429,
            reason=decision.reason,
            retry_after=decision.retry_after or 3,
        )

    acquired = await anti_spam_guard.acquire_global(action="api_chat")
    if not acquired:
        return error_response("busy", status=503, retry_after=5)

    try:
        user = await db.get_user(user_id)
        grade = payload.get("grade") or get_user_grade(user)
        result = await generate_tutor_response(user_id, text, grade=grade)
        if not result.busy:
            await db.record_request(user_id)
        return json_response({
            "ok": True,
            "text": result.text,
            "guided": result.guided,
            "used_rag": result.used_rag,
            "rag_confidence": result.rag_confidence,
            "rag_tasks": result.rag_tasks,
            "busy": result.busy,
            "auth_source": auth_source,
        })
    except Exception:
        logger.exception("Failed to handle API chat request")
        return error_response("internal_error", status=500)
    finally:
        anti_spam_guard.release_global(action="api_chat")


def setup_routes(app: web.Application) -> None:
    app.router.add_route("OPTIONS", "/{tail:.*}", handle_options)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/profile", handle_profile)
    app.router.add_get("/api/achievements", handle_achievements)
    app.router.add_get("/api/activity", handle_activity)
    app.router.add_get("/api/practice/task", handle_practice_task)
    app.router.add_post("/api/practice/answer", handle_practice_answer)
    app.router.add_post("/api/chat", handle_chat)
