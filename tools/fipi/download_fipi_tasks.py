#!/usr/bin/env python3
"""
Загрузка заданий из открытого банка ФИПИ (легально)
Источник: http://fipi.ru/
"""
import asyncio
import sys
import os

sys.path.insert(0, '/opt/tutor-bot/src')

import asyncpg
from parsers.task_loader import TaskLoader

# Примеры заданий для демонстрации (в реальности нужно парсить с fipi.ru)
SAMPLE_TASKS = [
    {
        'subject_code': 'math-profile',
        'year': 2024,
        'task_number': 11,
        'difficulty': 'profile',
        'topic': 'Производные',
        'subtopic': 'Нахождение производной',
        'condition': 'Найдите производную функции f(x) = x³ + 2x² - 5x + 1 в точке x = 2',
        'solution': '',  # Будем генерировать через ИИ
        'answer': '15',
        'source_url': 'http://fipi.ru/'
    },
    {
        'subject_code': 'math-profile',
        'year': 2024,
        'task_number': 12,
        'difficulty': 'profile',
        'topic': 'Производные',
        'subtopic': 'Исследование функции',
        'condition': 'Найдите точку минимума функции y = x³ - 3x² + 2',
        'solution': '',
        'answer': '2',
        'source_url': 'http://fipi.ru/'
    },
    {
        'subject_code': 'math-profile',
        'year': 2024,
        'task_number': 5,
        'difficulty': 'profile',
        'topic': 'Уравнения',
        'subtopic': 'Квадратные уравнения',
        'condition': 'Решите уравнение x² - 5x + 6 = 0. В ответе запишите больший корень.',
        'solution': '',
        'answer': '3',
        'source_url': 'http://fipi.ru/'
    },
]

async def main():
    print("🚀 Загрузка заданий ФИПИ (легально)...\n")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required")
    
    print("📥 Подключение к базе данных...")
    loader = TaskLoader(db_url)
    await loader.connect()
    
    # Загружаем примеры заданий
    print(f"💾 Загрузка {len(SAMPLE_TASKS)} заданий...")
    await loader.load_tasks(SAMPLE_TASKS)
    
    # Статистика
    stats = await loader.get_statistics()
    print(f"\n✅ Загружено задач: {stats}")
    
    await loader.close()
    print("\n✅ Загрузка завершена!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
