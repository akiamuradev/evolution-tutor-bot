#!/usr/bin/env python3
"""Загрузка открытых вариантов КИМ ЕГЭ 2026 с ФИПИ"""
import requests
import zipfile
import PyPDF2
import re
import asyncpg
import asyncio
import os
from pathlib import Path
import time

DOWNLOAD_DIR = Path("/tmp/fipi_kim")
DOWNLOAD_DIR.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://fipi.ru/',
}

BASE_URL = "https://doc.fipi.ru/ege/otkrytyy-bank-zadaniy-ege/otkrytyye-varianty-kim-ege/2026/"

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
    'german': ('Nem_1_ege2026.zip', 'Немецкий язык'),
    'french': ('Fran_1_ege2026.zip', 'Французский язык'),
    'spanish': ('Isp_1_ege2026.zip', 'Испанский язык'),
    'chinese': ('Kit_1_ege2026.zip', 'Китайский язык'),
}

def download_archives():
    """Скачивает все архивы"""
    print("📥 Скачиваю архивы с ФИПИ...")
    for code, (filename, name) in SUBJECTS.items():
        url = BASE_URL + filename
        zip_path = DOWNLOAD_DIR / filename
        
        if not zip_path.exists():
            print(f"  {name}...", end=' ', flush=True)
            time.sleep(3)
            try:
                response = requests.get(url, headers=HEADERS, timeout=120)
                if response.status_code == 200:
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ {len(response.content)} bytes")
                else:
                    print(f"❌ Status {response.status_code}")
            except Exception as e:
                print(f"❌ {e}")
        else:
            print(f"  {name}: ✅ уже скачан")

def extract_archives():
    """Распаковывает все архивы"""
    print("\n📦 Распаковываю архивы...")
    for code, (filename, name) in SUBJECTS.items():
        zip_path = DOWNLOAD_DIR / filename
        extract_dir = DOWNLOAD_DIR / filename.replace('.zip', '')
        
        if not extract_dir.exists() or not list(extract_dir.glob("*.pdf")):
            extract_dir.mkdir(exist_ok=True)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                pdfs = list(extract_dir.glob("*.pdf"))
                print(f"  ✅ {name}: {len(pdfs)} PDF")
            except Exception as e:
                print(f"  ❌ {name}: {e}")
        else:
            pdfs = list(extract_dir.glob("*.pdf"))
            print(f"  {name}: ✅ уже распакован ({len(pdfs)} PDF)")

def parse_pdf(pdf_path, subject_code, subject_name):
    """Парсит PDF и извлекает задачи"""
    tasks = []
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + "\n"
        
        # Ищем задания (паттерн: "Задание 1" или "1." в начале строки)
        # Это упрощённый парсер — нужно будет улучшить
        lines = full_text.split('\n')
        current_task = None
        task_text = []
        
        for line in lines:
            # Начало нового задания
            if re.match(r'^\s*(Задание\s+)?\d+[\.\)]\s*', line):
                if current_task:
                    tasks.append({
                        'subject': subject_code,
                        'subject_name': subject_name,
                        'condition': '\n'.join(task_text).strip(),
                        'answer': None,  # Ответы нужно искать отдельно
                        'solution': None,
                        'source': 'fipi_demo_2026'
                    })
                current_task = line
                task_text = [line]
            elif current_task:
                task_text.append(line)
        
        # Добавляем последнее задание
        if current_task:
            tasks.append({
                'subject': subject_code,
                'subject_name': subject_name,
                'condition': '\n'.join(task_text).strip(),
                'answer': None,
                'solution': None,
                'source': 'fipi_demo_2026'
            })
        
    except Exception as e:
        print(f"  ❌ Ошибка парсинга {pdf_path}: {e}")
    
    return tasks

async def save_to_db(tasks):
    """Сохраняет задачи в БД"""
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user=os.getenv('POSTGRES_USER', 'tutor_user'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'tutor_db')
    )
    
    # Получаем ID предметов
    subjects_map = {}
    rows = await conn.fetch("SELECT id, code FROM subjects")
    for row in rows:
        subjects_map[row['code']] = row['id']
    
    saved = 0
    for task in tasks:
        subject_id = subjects_map.get(task['subject'])
        if not subject_id:
            continue
        
        try:
            await conn.execute("""
                INSERT INTO fipi_tasks (subject_id, condition, answer, solution, topic)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
            """, subject_id, task['condition'], task['answer'], task['solution'], 
                'Демоверсия ЕГЭ 2026', task['source'])
            saved += 1
        except Exception as e:
            print(f"  ❌ Ошибка сохранения: {e}")
    
    await conn.close()
    return saved

def main():
    print("🚀 Загрузка открытых вариантов КИМ ЕГЭ 2026 с ФИПИ\n")
    
    # 1. Скачиваем архивы
    download_archives()
    
    # 2. Распаковываем
    extract_archives()
    
    # 3. Парсим PDF
    print("\n📄 Парсю PDF файлы...")
    all_tasks = []
    for code, (filename, name) in SUBJECTS.items():
        extract_dir = DOWNLOAD_DIR / filename.replace('.zip', '')
        if extract_dir.exists():
            for pdf_path in extract_dir.glob("*.pdf"):
                print(f"  {name}: {pdf_path.name}...", end=' ', flush=True)
                tasks = parse_pdf(pdf_path, code, name)
                print(f"✅ {len(tasks)} задач")
                all_tasks.extend(tasks)
    
    print(f"\n📊 Всего извлечено задач: {len(all_tasks)}")
    
    # 4. Сохраняем в БД
    if all_tasks:
        print("\n💾 Сохраняю в базу данных...")
        saved = asyncio.run(save_to_db(all_tasks))
        print(f"✅ Сохранено задач: {saved}")
    
    print("\n🎉 Готово!")

if __name__ == "__main__":
    main()
