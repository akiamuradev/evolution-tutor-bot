"""Парсер открытого банка заданий ФИПИ"""
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FIPIParser:
    """Парсер для загрузки заданий с различных источников"""
    
    def __init__(self):
        self.base_urls = {
            'math-profile': 'http://math100.ru/ege/',
            'math-base': 'http://math100.ru/oge/',
            # Добавляй другие источники
        }
    
    async def parse_math_tasks(self, subject_code: str = 'math-profile') -> List[Dict]:
        """
        Парсит задачи по математике с math100.ru
        Возвращает список задач в формате:
        {
            'subject_code': str,
            'year': int,
            'task_number': int,
            'difficulty': str,
            'topic': str,
            'condition': str,
            'solution': str,
            'answer': str
        }
        """
        tasks = []
        
        # Пример структуры - нужно адаптировать под реальный сайт
        async with aiohttp.ClientSession() as session:
            # Парсинг по номерам заданий (1-18 для ЕГЭ профиль)
            for task_num in range(1, 19):
                url = f"{self.base_urls.get(subject_code)}task{task_num}/"
                
                try:
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            html = await response.text()
                            task_data = await self._parse_task_page(html, task_num, subject_code)
                            if task_data:
                                tasks.extend(task_data)
                                logger.info(f"✅ Спаршено {len(task_data)} задач для задания {task_num}")
                        await asyncio.sleep(1)  # Чтобы не банили
                except Exception as e:
                    logger.error(f"❌ Ошибка парсинга задания {task_num}: {e}")
        
        return tasks
    
    async def _parse_task_page(self, html: str, task_number: int, subject_code: str) -> List[Dict]:
        """Парсит страницу с заданием"""
        tasks = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все задачи на странице (адаптируй селекторы под реальный сайт)
        task_blocks = soup.find_all('div', class_='task-block')
        
        for block in task_blocks:
            try:
                condition = block.find('div', class_='condition').get_text(strip=True)
                solution = block.find('div', class_='solution').get_text(strip=True) if block.find('div', class_='solution') else ""
                answer = block.find('div', class_='answer').get_text(strip=True) if block.find('div', class_='answer') else ""
                topic = block.find('div', class_='topic').get_text(strip=True) if block.find('div', class_='topic') else "Общая тема"
                
                tasks.append({
                    'subject_code': subject_code,
                    'year': 2024,  # Можно извлечь из страницы
                    'task_number': task_number,
                    'difficulty': 'profile' if 'profile' in subject_code else 'base',
                    'topic': topic,
                    'subtopic': "",
                    'condition': condition,
                    'solution': solution,
                    'answer': answer,
                    'source_url': ""
                })
            except Exception as e:
                logger.error(f"❌ Ошибка разбора блока задачи: {e}")
        
        return tasks
    
    async def parse_from_pdf(self, pdf_path: str, subject_code: str) -> List[Dict]:
        """
        Парсит PDF с демоверсиями ФИПИ
        Требуется библиотека pdfplumber или PyPDF2
        """
        import pdfplumber
        
        tasks = []
        
        with pdfplumber.open(pdf_path) as pdf:
            current_task = {}
            for page in pdf.pages:
                text = page.extract_text()
                # Логика разбора PDF (зависит от структуры)
                # Нужно адаптировать под формат ФИПИ
        
        return tasks
    
    async def parse_from_csv(self, csv_path: str) -> List[Dict]:
        """Загружает задачи из CSV (если найдёшь готовый датасет)"""
        import csv
        
        tasks = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tasks.append({
                    'subject_code': row.get('subject', 'unknown'),
                    'year': int(row.get('year', 2024)),
                    'task_number': int(row.get('task_number', 0)),
                    'difficulty': row.get('difficulty', 'base'),
                    'topic': row.get('topic', ''),
                    'subtopic': row.get('subtopic', ''),
                    'condition': row.get('condition', ''),
                    'solution': row.get('solution', ''),
                    'answer': row.get('answer', ''),
                    'source_url': row.get('source_url', '')
                })
        
        return tasks
