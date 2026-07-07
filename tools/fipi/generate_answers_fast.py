#!/usr/bin/env python3
"""Быстрая генерация ответов через ИИ (параллельная обработка)"""
import asyncio
import asyncpg
import httpx
import os
import time
from typing import Optional

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "qwen/qwen-2.5-72b-instruct"

async def generate_answer(condition: str, subject: str, topic: str, semaphore: asyncio.Semaphore) -> Optional[dict]:
    """Генерирует ответ через ИИ с ограничением параллелизма"""
    async with semaphore:
        prompt = f"""Ты — эксперт ЕГЭ по предмету "{subject}". Реши задачу и дай краткий ответ.

ТЕМА: {topic}

ЗАДАЧА:
{condition}

ФОРМАТ ОТВЕТА (строго следуй):
ОТВЕТ: [краткий ответ — число, слово, последовательность]
РЕШЕНИЕ: [пошаговое решение в 2-3 предложения]

Отвечай только на русском языке. Если задача на английском — переведи условие и реши."""
        
        for attempt in range(3):  # 3 попытки
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
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
                        
                        answer = None
                        solution = None
                        
                        if "ОТВЕТ:" in content:
                            answer = content.split("ОТВЕТ:")[1].split("РЕШЕНИЕ:")[0].strip()
                        if "РЕШЕНИЕ:" in content:
                            solution = content.split("РЕШЕНИЕ:")[1].strip()
                        
                        if answer:
                            return {"answer": answer, "solution": solution}
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"  ❌ Ошибка после 3 попыток: {e}")
        
        return None

async def process_task(task: dict, semaphore: asyncio.Semaphore, conn: asyncpg.Connection):
    """Обрабатывает одну задачу"""
    result = await generate_answer(task['condition'], task['subject'], task['topic'], semaphore)
    
    if result and result['answer']:
        await conn.execute("""
            UPDATE fipi_tasks
            SET answer = $1, solution = $2
            WHERE id = $3
        """, result['answer'], result['solution'], task['id'])
        return True, task['id'], result['answer'][:50]
    
    return False, task['id'], None

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
    
    # Получаем задачи без ответов
    tasks = await conn.fetch("""
        SELECT t.id, t.condition, s.name as subject, t.topic
        FROM fipi_tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE (t.answer IS NULL OR t.answer = '')
          AND s.code IN ('physics', 'biology', 'social-studies', 'english', 'informatics', 'russian')
        ORDER BY RANDOM()
    """)
    
    print(f"🚀 Начинаем быструю генерацию для {len(tasks)} задач...")
    print(f"⚡ Параллельность: 10 задач одновременно")
    
    # Ограничение параллелизма (10 задач одновременно)
    semaphore = asyncio.Semaphore(10)
    
    success_count = 0
    error_count = 0
    start_time = time.time()
    
    # Обрабатываем батчами по 100 задач
    batch_size = 100
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        
        # Создаём задачи для asyncio
        task_coroutines = [process_task(task, semaphore, conn) for task in batch]
        
        # Выполняем параллельно
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Считаем результаты
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                continue
            
            success, task_id, answer_preview = result
            if success:
                success_count += 1
            else:
                error_count += 1
        
        # Прогресс
        processed = i + len(batch)
        elapsed = time.time() - start_time
        speed = processed / elapsed if elapsed > 0 else 0
        eta = (len(tasks) - processed) / speed if speed > 0 else 0
        
        print(f"\n📊 Прогресс: {processed}/{len(tasks)} | ✅ {success_count} | ❌ {error_count} | ⚡ {speed:.1f} задач/сек | ETA: {eta/60:.0f} мин\n")
    
    print(f"\n🎉 Завершено! Успешно: {success_count}, Ошибок: {error_count}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
