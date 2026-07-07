import asyncio
import sqlite3
import asyncpg
import os
import re
from bs4 import BeautifulSoup

def clean_html_to_text(html_content):
    """Конвертирует HTML в читаемый текст с правильным форматированием таблиц"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Обрабатываем таблицы
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = []
            for td in tr.find_all(['td', 'th']):
                text = td.get_text(strip=True)
                cells.append(text)
            if cells:
                rows.append(' | '.join(cells))
        
        # Заменяем таблицу на текстовое представление
        if rows:
            table_text = '\n'.join(rows)
            table.replace_with(table_text)
    
    # Получаем чистый текст
    text = soup.get_text(separator=' ', strip=True)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_task_number(url):
    """Извлекает номер задания из URL"""
    match = re.search(r'qid=(\d+)', url)
    if match:
        return int(match.group(1))
    return 0

async def export_to_postgres_v2():
    sqlite_path = '/app/database/fipibank-problems.db'
    
    print(f"📂 Подключаемся к SQLite: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Получаем статистику
    sqlite_cursor.execute("SELECT COUNT(*) FROM fipibank_problems")
    total = sqlite_cursor.fetchone()[0]
    print(f"📊 Всего заданий в SQLite: {total}")
    
    # Получаем задания с темами из codifier_themes
    sqlite_cursor.execute("""
        SELECT DISTINCT p.problem_id, p.url, p.condition_html, 
               s.name as subject_name, gt.name as gia_type,
               ct.name as theme_name
        FROM fipibank_problems p
        JOIN fipibank_problems_subjects ps ON p.id = ps.fipibank_problem_id
        JOIN subjects s ON ps.subject_id = s.id
        JOIN fipibank_problems_gia_types pg ON p.id = pg.fipibank_problem_id
        JOIN gia_types gt ON pg.gia_type_id = gt.id
        LEFT JOIN fipibank_problems_codifier_themes pct ON p.id = pct.fipibank_problem_id
        LEFT JOIN codifier_themes ct ON pct.codifier_theme_id = ct.id
    """)
    
    problems = sqlite_cursor.fetchall()
    print(f"📋 Заданий для экспорта: {len(problems)}")
    
    # Подключаемся к PostgreSQL
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    
    # Маппинг предметов
    subject_mapping = {
        'Математика': 'math-profile',
        'Русский язык': 'russian',
        'Физика': 'physics',
        'Химия': 'chemistry',
        'Биология': 'biology',
        'История': 'history',
        'Обществознание': 'social-studies',
        'Информатика и ИКТ': 'informatics',
        'География': 'geography',
        'Литература': 'literature',
        'Английский язык': 'english',
    }
    
    loaded = 0
    skipped = 0
    errors = 0
    
    async with pool.acquire() as conn:
        for i, (problem_id, url, condition_html, subject_name, gia_type, theme_name) in enumerate(problems):
            try:
                # Определяем код предмета
                subject_code = subject_mapping.get(subject_name)
                if not subject_code:
                    skipped += 1
                    continue
                
                # Для ОГЭ используем math-base вместо math-profile
                if gia_type == 'oge' and subject_code == 'math-profile':
                    subject_code = 'math-base'
                
                # Извлекаем номер задания из URL (уже int)
                task_number = extract_task_number(url)
                
                # Конвертируем HTML в читаемый текст
                condition_text = clean_html_to_text(condition_html)
                
                # Пропускаем слишком короткие задания
                if len(condition_text) < 30:
                    skipped += 1
                    continue
                
                # Получаем ID предмета в нашей БД
                subj = await conn.fetchrow(
                    "SELECT id FROM subjects WHERE code = $1",
                    subject_code
                )
                if not subj:
                    skipped += 1
                    continue
                
                # Используем тему из codifier_themes или название предмета
                topic = theme_name if theme_name else f'{subject_name} ({gia_type.upper()})'
                
                # Вставляем задание
                await conn.execute("""
                    INSERT INTO fipi_tasks (
                        subject_id, year, task_number, difficulty,
                        topic, condition, solution, answer, source_url
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT DO NOTHING
                """,
                    subj['id'],
                    2024,
                    task_number,  # уже int
                    gia_type,
                    topic,
                    condition_text,
                    '',
                    '',
                    url
                )
                loaded += 1
                
                if loaded % 1000 == 0:
                    print(f"✅ Загружено: {loaded}")
            
            except Exception as e:
                errors += 1
                if errors < 5:
                    print(f"❌ Ошибка: {e}")
    
    await pool.close()
    sqlite_conn.close()
    
    print(f"\n🎉 ЭКСПОРТ V2 ЗАВЕРШЁН!")
    print(f"   ✅ Успешно загружено: {loaded}")
    print(f"   ⏭️ Пропущено: {skipped}")
    print(f"   ❌ Ошибок: {errors}")
    
    # Финальная статистика
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT subject_id) as subjects,
                   COUNT(DISTINCT topic) as topics
            FROM fipi_tasks
        """)
        print(f"\n📊 ИТОГО в базе бота:")
        print(f"   • Заданий: {stats['total']}")
        print(f"   • Предметов: {stats['subjects']}")
        print(f"   • Уникальных тем: {stats['topics']}")
        
        # Распределение по предметам
        rows = await conn.fetch("""
            SELECT s.name, s.code, COUNT(t.id) as count
            FROM subjects s
            LEFT JOIN fipi_tasks t ON s.id = t.subject_id
            GROUP BY s.name, s.code
            ORDER BY count DESC
        """)
        print("\n📚 Распределение по предметам:")
        for row in rows:
            if row['count'] > 0:
                print(f"   • {row['name']}: {row['count']}")
    await pool.close()

asyncio.run(export_to_postgres_v2())
