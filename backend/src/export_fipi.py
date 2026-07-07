import asyncio
import sqlite3
import asyncpg
import os
from bs4 import BeautifulSoup

async def export_to_postgres():
    sqlite_path = '/app/database/fipibank-problems.db'
    
    print(f"📂 Подключаемся к SQLite: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Получаем статистику
    sqlite_cursor.execute("SELECT COUNT(*) FROM fipibank_problems")
    total = sqlite_cursor.fetchone()[0]
    print(f"📊 Всего заданий в SQLite: {total}")
    
    # Получаем все задания с предметами (используем правильные названия таблиц)
    sqlite_cursor.execute("""
        SELECT DISTINCT p.problem_id, p.url, p.condition_html, 
               s.name as subject_name, gt.name as gia_type
        FROM fipibank_problems p
        JOIN fipibank_problems_subjects ps ON p.id = ps.fipibank_problem_id
        JOIN subjects s ON ps.subject_id = s.id
        JOIN fipibank_problems_gia_types pg ON p.id = pg.fipibank_problem_id
        JOIN gia_types gt ON pg.gia_type_id = gt.id
    """)
    
    problems = sqlite_cursor.fetchall()
    print(f"📋 Заданий для экспорта: {len(problems)}")
    
    # Подключаемся к PostgreSQL
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    
    # Маппинг предметов ФИПИ → наш код
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
        for i, (problem_id, url, condition_html, subject_name, gia_type) in enumerate(problems):
            try:
                # Определяем код предмета
                subject_code = subject_mapping.get(subject_name)
                if not subject_code:
                    skipped += 1
                    continue
                
                # Для ОГЭ используем math-base вместо math-profile
                if gia_type == 'oge' and subject_code == 'math-profile':
                    subject_code = 'math-base'
                
                # Извлекаем чистый текст из HTML
                soup = BeautifulSoup(condition_html, 'html.parser')
                condition_text = soup.get_text(separator='\n', strip=True)
                
                # Пропускаем слишком короткие задания
                if len(condition_text) < 20:
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
                    0,
                    gia_type,
                    f'{subject_name} ({gia_type.upper()})',
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
    
    print(f"\n🎉 ЭКСПОРТ ЗАВЕРШЁН!")
    print(f"   ✅ Успешно загружено: {loaded}")
    print(f"   ⏭️ Пропущено: {skipped}")
    print(f"   ❌ Ошибок: {errors}")
    
    # Финальная статистика
    pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT subject_id) as subjects
            FROM fipi_tasks
        """)
        print(f"\n📊 ИТОГО в базе бота: {stats['total']} заданий по {stats['subjects']} предметам")
        
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

asyncio.run(export_to_postgres())
