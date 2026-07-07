import asyncio
import asyncpg
import os
import re
from html import unescape

async def cleanup_conditions():
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user=os.getenv('POSTGRES_USER', 'tutor_user'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'tutor_db')
    )
    
    # Получаем все задачи
    tasks = await conn.fetch("SELECT id, condition FROM fipi_tasks")
    
    cleaned_count = 0
    for task in tasks:
        condition = task['condition']
        if not condition:
            continue
        
        # Удаляем HTML теги
        clean = re.sub(r'<[^>]+>', ' ', condition)
        
        # Декодируем HTML entities
        clean = unescape(clean)
        
        # Удаляем лишние пробелы и переносы
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Удаляем дубликаты вариантов ответов (если есть)
        # Ищем паттерн "1) ... 2) ... 3) ..." и убираем дубликаты
        lines = clean.split('|')
        if len(lines) > 1:
            # Берём только первую часть (до первого |)
            clean = lines[0].strip()
        
        # Обновляем в БД
        if clean != condition:
            await conn.execute(
                "UPDATE fipi_tasks SET condition = $1 WHERE id = $2",
                clean, task['id']
            )
            cleaned_count += 1
    
    print(f"✅ Очищено условий: {cleaned_count} из {len(tasks)}")
    
    await conn.close()

asyncio.run(cleanup_conditions())
