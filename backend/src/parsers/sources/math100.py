"""
Парсер сайта Math100.ru
Специализированный источник для математики
Источники:
- http://math100.ru/ege/ (ЕГЭ профиль)
- http://math100.ru/oge/ (ОГЭ)
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class Math100Parser:
    """Парсер Math100.ru для математики"""
    
    URLS = {
        'math-profile': 'http://math100.ru/ege/',
        'math-base': 'http://math100.ru/oge/',
    }
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def parse_all_tasks(self, subject_code: str = 'math-profile') -> List[Dict]:
        """Парсит все задачи по математике"""
        if subject_code not in self.URLS:
            return []
        
        base_url = self.URLS[subject_code]
        all_tasks = []
        
        try:
            async with self.session:
                # Парсим по номерам заданий (1-18 для ЕГЭ, 1-25 для ОГЭ)
                max_task = 18 if 'profile' in subject_code else 25
                
                for task_num in range(1, max_task + 1):
                    url = f"{base_url}task{task_num}/"
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            tasks = await self._parse_task_page(html, task_num, subject_code)
                            all_tasks.extend(tasks)
                            logger.info(f"✅ Спаршено {len(tasks)} задач для задания {task_num}")
                        
                        await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Math100: {e}")
        
        return all_tasks
    
    async def _parse_task_page(self, html: str, task_number: int, subject_code: str) -> List[Dict]:
        """Парсит страницу с заданием"""
        tasks = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ищем все задачи на странице
        task_blocks = soup.find_all('div', class_='task') or soup.find_all('div', class_='problem')
        
        for block in task_blocks:
            try:
                condition = block.find('div', class_='condition') or block.find('div', class_='text')
                solution = block.find('div', class_='solution')
                answer = block.find('div', class_='answer')
                
                condition_text = condition.get_text(strip=True) if condition else ""
                solution_text = solution.get_text(strip=True) if solution else ""
                answer_text = answer.get_text(strip=True) if answer else ""
                
                if condition_text:
                    tasks.append({
                        'subject_code': subject_code,
                        'year': 2024,
                        'task_number': task_number,
                        'difficulty': 'profile' if 'profile' in subject_code else 'base',
                        'topic': f"Задание {task_number}",
                        'subtopic': '',
                        'condition': condition_text,
                        'solution': solution_text,
                        'answer': answer_text,
                        'source_url': ''
                    })
            except Exception as e:
                logger.error(f"❌ Ошибка разбора блока: {e}")
        
        return tasks
