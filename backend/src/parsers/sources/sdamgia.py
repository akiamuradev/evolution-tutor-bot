"""
Парсер сайта РешуЕГЭ/РешуОГЭ (sdamgia.ru)
Один из лучших источников с готовыми решениями
Источники:
- https://math-ege.sdamgia.ru/ (математика ЕГЭ)
- https://math-oge.sdamgia.ru/ (математика ОГЭ)
- https://rus-ege.sdamgia.ru/ (русский язык)
- https://phys-ege.sdamgia.ru/ (физика)
- https://bio-ege.sdamgia.ru/ (биология)
- https://hist-ege.sdamgia.ru/ (история)
- https://soc-ege.sdamgia.ru/ (обществознание)
- https://inf-ege.sdamgia.ru/ (информатика)
- https://geo-ege.sdamgia.ru/ (география)
- https://lit-ege.sdamgia.ru/ (литература)
- https://chem-ege.sdamgia.ru/ (химия)
- https://en-ege.sdamgia.ru/ (английский)
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class SdamgiaParser:
    """Парсер РешуЕГЭ/РешуОГЭ"""
    
    SUBJECTS = {
        'math-profile': 'https://math-ege.sdamgia.ru',
        'math-base': 'https://math-oge.sdamgia.ru',
        'russian': 'https://rus-ege.sdamgia.ru',
        'physics': 'https://phys-ege.sdamgia.ru',
        'chemistry': 'https://chem-ege.sdamgia.ru',
        'biology': 'https://bio-ege.sdamgia.ru',
        'history': 'https://hist-ege.sdamgia.ru',
        'social-studies': 'https://soc-ege.sdamgia.ru',
        'informatics': 'https://inf-ege.sdamgia.ru',
        'geography': 'https://geo-ege.sdamgia.ru',
        'literature': 'https://lit-ege.sdamgia.ru',
        'english': 'https://en-ege.sdamgia.ru',
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
    
    async def parse_subject_tasks(self, subject_code: str, limit: int = 100) -> List[Dict]:
        """
        Парсит задачи по предмету
        """
        if subject_code not in self.SUBJECTS:
            logger.error(f"❌ Предмет {subject_code} не найден")
            return []
        
        base_url = self.SUBJECTS[subject_code]
        tasks = []
        
        try:
            async with self.session:
                # Загружаем каталог заданий
                catalog_url = f"{base_url}/test"
                async with self.session.get(catalog_url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Ошибка загрузки {catalog_url}")
                        return tasks
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем ссылки на задания
                    task_links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/problem.php?id=' in href or '/task/' in href:
                            task_links.append(href)
                    
                    logger.info(f"✅ Найдено {len(task_links)} ссылок на задания")
                    
                    # Парсим каждое задание (ограничиваем limit)
                    for i, task_url in enumerate(task_links[:limit]):
                        if not task_url.startswith('http'):
                            task_url = base_url + task_url
                        
                        task = await self._parse_task_page(task_url, subject_code)
                        if task:
                            tasks.append(task)
                        
                        if (i + 1) % 10 == 0:
                            logger.info(f"📥 Спаршено {i+1}/{min(limit, len(task_links))} задач")
                        
                        await asyncio.sleep(0.5)  # Чтобы не банили
        
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга предмета {subject_code}: {e}")
        
        return tasks
    
    async def _parse_task_page(self, url: str, subject_code: str) -> Optional[Dict]:
        """Парсит страницу с конкретным заданием"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Извлекаем данные
                condition = self._extract_condition(soup)
                solution = self._extract_solution(soup)
                answer = self._extract_answer(soup)
                topic = self._extract_topic(soup)
                task_number = self._extract_task_number(url)
                
                if not condition:
                    return None
                
                return {
                    'subject_code': subject_code,
                    'year': self._extract_year(soup),
                    'task_number': task_number,
                    'difficulty': 'profile' if 'ege' in url else 'base',
                    'topic': topic,
                    'subtopic': '',
                    'condition': condition,
                    'solution': solution,
                    'answer': answer,
                    'source_url': url
                }
        
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга страницы {url}: {e}")
            return None
    
    def _extract_condition(self, soup: BeautifulSoup) -> str:
        """Извлекает условие задачи"""
        # Адаптируй селекторы под реальную структуру Sdamgia
        condition_div = soup.find('div', class_='task_text') or soup.find('div', class_='condition')
        return condition_div.get_text(strip=True) if condition_div else ""
    
    def _extract_solution(self, soup: BeautifulSoup) -> str:
        """Извлекает решение"""
        solution_div = soup.find('div', class_='solution') or soup.find('div', class_='rezsh')
        return solution_div.get_text(strip=True) if solution_div else ""
    
    def _extract_answer(self, soup: BeautifulSoup) -> str:
        """Извлекает ответ"""
        answer_div = soup.find('div', class_='answer') or soup.find('div', class_='otvet')
        return answer_div.get_text(strip=True) if answer_div else ""
    
    def _extract_topic(self, soup: BeautifulSoup) -> str:
        """Извлекает тему задачи"""
        topic_div = soup.find('div', class_='topic') or soup.find('div', class_='rubricator')
        return topic_div.get_text(strip=True) if topic_div else "Общая тема"
    
    def _extract_task_number(self, url: str) -> int:
        """Извлекает номер задания из URL"""
        match = re.search(r'id=(\d+)', url)
        return int(match.group(1)) if match else 0
    
    def _extract_year(self, soup: BeautifulSoup) -> int:
        """Извлекает год"""
        # Ищем год в тексте страницы
        year_div = soup.find('div', class_='year')
        if year_div:
            match = re.search(r'(\d{4})', year_div.get_text())
            if match:
                return int(match.group(1))
        return 2024  # По умолчанию
