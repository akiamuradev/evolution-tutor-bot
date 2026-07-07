#!/usr/bin/env python3
"""Генерация ответов для задач через ИИ"""
import asyncio
import asyncpg
import httpx
import json
import os
import time
from typing import Optional

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "qwen/qwen-2.5-72b-instruct"

async def generate_answer(condition: str, subject: str, topic: str) -> Optional[dict]:
    """Генерирует ответ через ИИ"""
    prompt = f"""Ты — эксперт ЕГЭ по предмету "{subject}". Реши задачу и дай краткий ответ.

ТЕМА: {topic}

ЗАДАЧА:
{condition}

ФОРМАТ ОТВЕТА (строго следуй):
ОТВЕТ: [краткий ответ — число, слово, последовательность]
РЕШЕНИЕ: [пошаговое решение в 2-3 предложения]

Отвечай только на русском языке. Если задача на английском — переведи условие и реши."""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Парсим ответ
                answer = None
                solution = None
                
                if "ОТВЕТ:" in content:
                    answer = content.split("ОТВЕТ:")[1].split("РЕШЕНИЕ:")[0].strip()
                if "РЕШЕНИЕ:" in content:
                    solution = content.split("РЕШЕНИЕ:")[1].strip()
                
                return {"answer": answer, "solution": solution}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    return None

async def main():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is required")

    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user=os.getenv('POSTGRES_USER', 'tutor_user'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'tutor_db')
    )
    
    # Получаем задачи без ответов (только 6 основных предметов)
    tasks = await conn.fetch("""
        SELECT t.id, t.condition, s.name as subject, t.topic
        FROM fipi_tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE (t.answer IS NULL OR t.answer = '')
          AND s.code IN ('physics', 'biology', 'social-studies', 'english', 'informatics', 'russian')
        ORDER BY RANDOM()
        LIMIT 2000
    """)
    
    print(f"🚀 Начинаем генерацию ответов для {len(tasks)} задач...")
    
    success_count = 0
    error_count = 0
    
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] Задача {task['id']} ({task['subject']})...")
        
        result = await generate_answer(task['condition'], task['subject'], task['topic'])
        
        if result and result['answer']:
            await conn.execute("""
                UPDATE fipi_tasks
                SET answer = $1, solution = $2
                WHERE id = $3
            """, result['answer'], result['solution'], task['id'])
            success_count += 1
            print(f"  ✅ Ответ: {result['answer'][:50]}...")
        else:
            error_count += 1
            print(f"  ❌ Не удалось сгенерировать")
        
        # Задержка, чтобы не превысить лимиты API
        await asyncio.sleep(1)
        
        # Каждые 100 задач — статистика
        if i % 100 == 0:
            print(f"\n📊 Прогресс: {i}/{len(tasks)} | ✅ Успешно: {success_count} | ❌ Ошибок: {error_count}\n")
    
    print(f"\n🎉 Завершено! Успешно: {success_count}, Ошибок: {error_count}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
