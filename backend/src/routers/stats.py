from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from ..services import db


router = Router()


@router.message(Command("stats"))
async def cmd_stats(m: types.Message):
    """Показать статистику ученика"""
    async with db.pool.acquire() as conn:
        # Общая статистика
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_correct) as correct,
                COUNT(DISTINCT subject_id) as subjects,
                COUNT(DISTINCT topic) as topics,
                COUNT(*) FILTER (WHERE used_explanation) as used_explanation
            FROM student_progress
            WHERE user_id = $1
        """, m.from_user.id)
        
        if stats['total'] == 0:
            await m.answer("📊 У тебя пока нет статистики.\n\nНапиши /practice чтобы начать!")
            return
        
        total = stats['total']
        correct = stats['correct']
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Прогресс-бар
        bar_length = 20
        filled = int(bar_length * accuracy / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Статистика по предметам
        subject_stats = await conn.fetch("""
            SELECT s.name, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct
            FROM student_progress sp
            JOIN subjects s ON sp.subject_id = s.id
            WHERE sp.user_id = $1
            GROUP BY s.name
            ORDER BY total DESC
            LIMIT 5
        """, m.from_user.id)
        
        # Достижения
        achievements_list = await conn.fetch("""
            SELECT achievement_name, earned_at
            FROM achievements
            WHERE user_id = $1
            ORDER BY earned_at DESC
        """, m.from_user.id)
        
        response = f"📊 ТВОЯ СТАТИСТИКА\n\n"
        response += f"📝 Решено задач: {total}\n"
        response += f"✅ Правильных: {correct} ({accuracy:.1f}%)\n"
        response += f"📚 Предметов: {stats['subjects']}\n"
        response += f"🎯 Тем изучено: {stats['topics']}\n"
        response += f"💡 Использовал объяснений: {stats['used_explanation']}\n\n"
        
        response += f"📈 Точность:\n{bar} {accuracy:.1f}%\n\n"
        
        if subject_stats:
            response += f"📚 По предметам:\n"
            for subj in subject_stats:
                subj_accuracy = (subj['correct'] / subj['total'] * 100) if subj['total'] > 0 else 0
                response += f"  • {subj['name']}: {subj['correct']}/{subj['total']} ({subj_accuracy:.0f}%)\n"
            response += "\n"
        
        if achievements_list:
            response += f"🏅 Достижения ({len(achievements_list)}):\n"
            for ach in achievements_list[:5]:  # Показываем последние 5
                response += f"  • {ach['achievement_name']}\n"
        
        await m.answer(response)


@router.callback_query(F.data == "show_stats")
async def show_stats_callback(c: CallbackQuery):
    """Показать статистику через кнопку"""
    await c.answer()
    
    async with db.pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_correct) as correct,
                COUNT(DISTINCT subject_id) as subjects,
                COUNT(DISTINCT topic) as topics,
                COUNT(*) FILTER (WHERE used_explanation) as used_explanation
            FROM student_progress
            WHERE user_id = $1
        """, c.from_user.id)
        
        if stats['total'] == 0:
            await c.message.answer("📊 У тебя пока нет статистики.\n\nНапиши /practice чтобы начать!")
            return
        
        total = stats['total']
        correct = stats['correct']
        accuracy = (correct / total * 100) if total > 0 else 0
        
        bar_length = 20
        filled = int(bar_length * accuracy / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        subject_stats = await conn.fetch("""
            SELECT s.name, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE is_correct) as correct
            FROM student_progress sp
            JOIN subjects s ON sp.subject_id = s.id
            WHERE sp.user_id = $1
            GROUP BY s.name
            ORDER BY total DESC
            LIMIT 5
        """, c.from_user.id)
        
        achievements_list = await conn.fetch("""
            SELECT achievement_name, earned_at
            FROM achievements
            WHERE user_id = $1
            ORDER BY earned_at DESC
        """, c.from_user.id)
        
        response = f"📊 ТВОЯ СТАТИСТИКА\n\n"
        response += f"📝 Решено задач: {total}\n"
        response += f"✅ Правильных: {correct} ({accuracy:.1f}%)\n"
        response += f"📚 Предметов: {stats['subjects']}\n"
        response += f"🎯 Тем изучено: {stats['topics']}\n"
        response += f"💡 Использовал объяснений: {stats['used_explanation']}\n\n"
        
        response += f"📈 Точность:\n{bar} {accuracy:.1f}%\n\n"
        
        if subject_stats:
            response += f"📚 По предметам:\n"
            for subj in subject_stats:
                subj_accuracy = (subj['correct'] / subj['total'] * 100) if subj['total'] > 0 else 0
                response += f"  • {subj['name']}: {subj['correct']}/{subj['total']} ({subj_accuracy:.0f}%)\n"
            response += "\n"
        
        if achievements_list:
            response += f"🏅 Достижения ({len(achievements_list)}):\n"
            for ach in achievements_list[:5]:
                response += f"  • {ach['achievement_name']}\n"
        
        await c.message.answer(response)
