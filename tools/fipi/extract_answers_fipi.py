#!/usr/bin/env python3
"""Извлечение ответов из PDF демоверсий ФИПИ"""
import PyPDF2
import re
import asyncpg
import asyncio
import os
from pathlib import Path

DOWNLOAD_DIR = Path("/tmp/fipi_kim")

SUBJECTS = {
    'russian': ('Rus_1_ege2026.zip', 'Русский язык'),
    'math-profile': ('Mat_1_ege2026.zip', 'Математика (профиль)'),
    'physics': ('Fiz_1_ege2026.zip', 'Физика'),
    'chemistry': ('Him_1_ege2026.zip', 'Химия'),
    'informatics': ('Inf_1_ege2026.zip', 'Информатика'),
    'biology': ('Bio_1_ege2026.zip', 'Биология'),
    'history': ('Ist_1_ege2026.zip', 'История'),
    'geography': ('Geo_1_ege2026.zip', 'География'),
    'social-studies': ('Ob_1_ege2026.zip', 'Обществознание'),
    'literature': ('Lit_1_ege2026.zip', 'Литература'),
    'english': ('Angl_1_ege2026.zip', 'Английский язык'),
}

def extract_answers_from_pdf(pdf_path):
    """Извлекает ответы из PDF"""
    answers = {}
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        
        # Ищем раздел "Ответы" или "Ключи"
        # Паттерны: "Ответы:", "Ключи:", "Ответы к заданиям"
        answer_sections = re.findall(
            r'(?:Ответы|Ключи|Ответы к заданиям)[:\s]*(.*?)(?:\n\n|\Z)',
            full_text,
            re.DOTALL | re.IGNORECASE
        )
        
        for section in answer_sections:
            # Ищем паттерны: "1. 42" или "Задание 1: 42" или "1) 42"
            matches = re.findall(
                r'(?:Задание\s+)?(\d+)[\.\)\:]\s*([^\n]+)',
                section
            )
            
            for task_num, answer in matches:
                answer = answer.strip()
                if answer and len(answer) < 200:  # Фильтруем мусор
                    answers[int(task_num)] = answer
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    return answers

async def update_answers_in_db(subject_code, answers):
    """Обновляет ответы в БД"""
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user=os.getenv('POSTGRES_USER', 'tutor_user'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'tutor_db')
    )
    
    # Получаем subject_id
    subject_row = await conn.fetchrow(
        "SELECT id FROM subjects WHERE code = $1",
        subject_code
    )
    
    if not subject_row:
        await conn.close()
        return 0
    
    subject_id = subject_row['id']
    
    # Получаем задачи этого предмета
    tasks = await conn.fetch("""
        SELECT id, condition
        FROM fipi_tasks
        WHERE subject_id = $1 AND (answer IS NULL OR answer = '')
        ORDER BY id
    """, subject_id)
    
    updated = 0
    for i, task in enumerate(tasks, 1):
        if i in answers:
            await conn.execute("""
                UPDATE fipi_tasks
                SET answer = $1
                WHERE id = $2
            """, answers[i], task['id'])
            updated += 1
    
    await conn.close()
    return updated

def main():
    print("🔍 Извлечение ответов из PDF демоверсий ФИПИ\n")
    
    total_updated = 0
    
    for code, (filename, name) in SUBJECTS.items():
        extract_dir = DOWNLOAD_DIR / filename.replace('.zip', '')
        
        if not extract_dir.exists():
            print(f"  {name}: ❌ Папка не найдена")
            continue
        
        print(f"  {name}...", end=' ', flush=True)
        
        # Ищем PDF с ответами
        answer_pdfs = list(extract_dir.glob("*answer*.pdf")) + \
                      list(extract_dir.glob("*key*.pdf")) + \
                      list(extract_dir.glob("*res*.pdf"))
        
        if not answer_pdfs:
            # Если отдельного файла с ответами нет — ищем в основном PDF
            pdfs = list(extract_dir.glob("*.pdf"))
            if pdfs:
                answer_pdfs = pdfs
        
        subject_answers = {}
        for pdf_path in answer_pdfs:
            answers = extract_answers_from_pdf(pdf_path)
            subject_answers.update(answers)
        
        if subject_answers:
            updated = asyncio.run(update_answers_in_db(code, subject_answers))
            print(f"✅ {len(subject_answers)} ответов, обновлено {updated}")
            total_updated += updated
        else:
            print("❌ Ответы не найдены")
    
    print(f"\n🎉 Готово! Обновлено ответов: {total_updated}")

if __name__ == "__main__":
    main()
