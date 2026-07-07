from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from ..services import db


router = Router()


@router.message(Command("plan"))
async def cmd_plan(m: types.Message):
    """Генерирует персональный план подготовки"""
    async with db.pool.acquire() as conn:
        # Проверяем, есть ли свежий план (менее 7 дней)
        existing_plan = await conn.fetchrow("""
            SELECT plan_text, created_at
            FROM study_plans
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 1
        """, m.from_user.id)
        
        if existing_plan:
            await m.answer(f"📋 ТВОЙ ПЛАН (актуален до {existing_plan['created_at'].strftime('%d.%m.%Y')})\n\n{existing_plan['plan_text']}")
            return
        
        # Собираем статистику для анализа
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_correct) as correct,
                COUNT(DISTINCT subject_id) as subjects
            FROM student_progress
            WHERE user_id = $1
        """, m.from_user.id)
        
        if stats['total'] < 5:
            await m.answer("📋 Для составления плана нужно решить минимум 5 задач.\n\nНапиши /practice чтобы начать!")
            return
        
        # Анализируем слабые темы
        weak_topics = await conn.fetch("""
            SELECT topic, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct,
                   ROUND(COUNT(*) FILTER (WHERE is_correct)::numeric / COUNT(*) * 100, 1) as accuracy
            FROM student_progress
            WHERE user_id = $1
            GROUP BY topic
            HAVING COUNT(*) >= 2
            ORDER BY accuracy ASC
            LIMIT 5
        """, m.from_user.id)
        
        # Анализируем сильные темы
        strong_topics = await conn.fetch("""
            SELECT topic, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct,
                   ROUND(COUNT(*) FILTER (WHERE is_correct)::numeric / COUNT(*) * 100, 1) as accuracy
            FROM student_progress
            WHERE user_id = $1
            GROUP BY topic
            HAVING COUNT(*) >= 2
            ORDER BY accuracy DESC
            LIMIT 3
        """, m.from_user.id)
        
        # Формируем промпт для ИИ
        weak_topics_text = "\n".join([f"  • {t['topic']}: {t['accuracy']}% ({t['correct']}/{t['total']})" for t in weak_topics])
        strong_topics_text = "\n".join([f"  • {t['topic']}: {t['accuracy']}% ({t['correct']}/{t['total']})" for t in strong_topics])
        
        prompt = f"""Ты — образовательный консультант. Составь персональный план подготовки на неделю для ученика.

Статистика ученика:
- Всего решено задач: {stats['total']}
- Правильных: {stats['correct']} ({stats['correct']/stats['total']*100:.1f}%)
- Предметов: {stats['subjects']}

Слабые темы (нужно улучшить):
{weak_topics_text}

Сильные темы (хорошо знает):
{strong_topics_text}

Составь план на 7 дней:
- Конкретные задачи на каждый день
- Сколько времени уделять
- Какие темы повторить
- Какие новые темы изучить

Пиши кратко, по делу, с мотивацией."""
        
        from .generation import generate_with_cancel

        # Генерируем план с кнопкой отмены
        plan_text, was_cancelled = await generate_with_cancel(
            m, prompt,
            thinking_text="Составляю персональный план...",
            animations=["📋", "📋.", "📋..", "📋...", "📊", "📊.", "📊..", "📊..."],
            kind="study_plan",
        )
        
        if was_cancelled:
            return
        
        # Сохраняем план в БД
        await conn.execute("""
            INSERT INTO study_plans (user_id, plan_text)
            VALUES ($1, $2)
        """, m.from_user.id, plan_text)
        
        await m.answer(f"📋 ТВОЙ ПЛАН НА НЕДЕЛЮ\n\n{plan_text}")


@router.callback_query(F.data == "show_plan")
async def show_plan_callback(c: CallbackQuery):
    """Показать план через кнопку"""
    await c.answer()
    
    async with db.pool.acquire() as conn:
        existing_plan = await conn.fetchrow("""
            SELECT plan_text, created_at
            FROM study_plans
            WHERE user_id = $1 AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 1
        """, c.from_user.id)
        
        if existing_plan:
            await c.message.answer(f"📋 ТВОЙ ПЛАН (актуален до {existing_plan['created_at'].strftime('%d.%m.%Y')})\n\n{existing_plan['plan_text']}")
            return
        
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_correct) as correct,
                COUNT(DISTINCT subject_id) as subjects
            FROM student_progress
            WHERE user_id = $1
        """, c.from_user.id)
        
        if stats['total'] < 5:
            await c.message.answer("📋 Для составления плана нужно решить минимум 5 задач.\n\nНапиши /practice чтобы начать!")
            return
        
        weak_topics = await conn.fetch("""
            SELECT topic, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct,
                   ROUND(COUNT(*) FILTER (WHERE is_correct)::numeric / COUNT(*) * 100, 1) as accuracy
            FROM student_progress
            WHERE user_id = $1
            GROUP BY topic
            HAVING COUNT(*) >= 2
            ORDER BY accuracy ASC
            LIMIT 5
        """, c.from_user.id)
        
        strong_topics = await conn.fetch("""
            SELECT topic, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct,
                   ROUND(COUNT(*) FILTER (WHERE is_correct)::numeric / COUNT(*) * 100, 1) as accuracy
            FROM student_progress
            WHERE user_id = $1
            GROUP BY topic
            HAVING COUNT(*) >= 2
            ORDER BY accuracy DESC
            LIMIT 3
        """, c.from_user.id)
        
        weak_topics_text = "\n".join([f"  • {t['topic']}: {t['accuracy']}% ({t['correct']}/{t['total']})" for t in weak_topics])
        strong_topics_text = "\n".join([f"  • {t['topic']}: {t['accuracy']}% ({t['correct']}/{t['total']})" for t in strong_topics])
        
        prompt = f"""Ты — образовательный консультант. Составь персональный план подготовки на неделю для ученика.

Статистика ученика:
- Всего решено задач: {stats['total']}
- Правильных: {stats['correct']} ({stats['correct']/stats['total']*100:.1f}%)
- Предметов: {stats['subjects']}

Слабые темы (нужно улучшить):
{weak_topics_text}

Сильные темы (хорошо знает):
{strong_topics_text}

Составь план на 7 дней:
- Конкретные задачи на каждый день
- Сколько времени уделять
- Какие темы повторить
- Какие новые темы изучить

Пиши кратко, по делу, с мотивацией."""
        
        from .generation import generate_with_cancel

        plan_text, was_cancelled = await generate_with_cancel(
            c.message, prompt,
            thinking_text="Составляю персональный план...",
            animations=["📋", "📋.", "📋..", "📋...", "📊", "📊.", "📊..", "📊..."],
            kind="study_plan",
        )
        
        if was_cancelled:
            return
        
        await conn.execute("""
            INSERT INTO study_plans (user_id, plan_text)
            VALUES ($1, $2)
        """, c.from_user.id, plan_text)
        
        await c.message.answer(f"📋 ТВОЙ ПЛАН НА НЕДЕЛЮ\n\n{plan_text}")
