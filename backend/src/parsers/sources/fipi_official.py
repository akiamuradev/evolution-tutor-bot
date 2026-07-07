"""
Парсер официального сайта ФИПИ
Источники:
- http://fipi.ru/ege-i-gve-11/demoversii-specifikacii-kodifikatory
- http://fipi.ru/oge-i-gve-9/demoversii-specifikacii-kodifikatory
- Открытый банк заданий: http://fipi.ru/
"""
import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class FIPIOfficialParser:
    """Парсер официального сайта ФИПИ"""
    
    BASE_URL = "http://fipi.ru"
    
    SUBJECTS_EGE = {
        'math-profile': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'russian': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'physics': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'chemistry': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'biology': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'history': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'social-studies': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'english': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'informatics': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'geography': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
        'literature': '/ege-i-gve-11/demoversii-specifikacii-kodifikatory',
    }
    
    SUBJECTS_OGE = {
        'math-base': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'russian-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'physics-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'chemistry-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'biology-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'history-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'social-studies-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'english-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'informatics-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'geography-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
        'literature-oge': '/oge-i-gve-9/demoversii-specifikacii-kodifikatory',
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
    
    async def download_demoversion(self, subject_code: str, year: int = 2025) -> Optional[Dict]:
        """
        Скачивает демоверсию, спецификатор и кодификатор
        Возвращает ссылки на PDF файлы
        """
        subjects = self.SUBJECTS_EGE if 'oge' not in subject_code else self.SUBJECTS_OGE
        
        if subject_code not in subjects:
            logger.error(f"❌ Предмет {subject_code} не найден")
            return None
        
        url = self.BASE_URL + subjects[subject_code]
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"❌ Ошибка загрузки {url}: {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Ищем ссылки на PDF для указанного года
                demoversion_url = None
                specifikator_url = None
                kodifikator_url = None
                
                for link in soup.find_all('a', href=True):
                    href = link['href'].lower()
                    text = link.get_text().lower()
                    
                    if str(year) in href or str(year) in text:
                        if 'демо' in text or 'demo' in href:
                            demoversion_url = link['href']
                        elif 'спецификатор' in text or 'spec' in href:
                            specifikator_url = link['href']
                        elif 'кодификатор' in text or 'codif' in href:
                            kodifikator_url = link['href']
                
                # Делаем абсолютные URL
                demoversion_url = self.BASE_URL + demoversion_url if demoversion_url and demoversion_url.startswith('/') else demoversion_url
                specifikator_url = self.BASE_URL + specifikator_url if specifikator_url and specifikator_url.startswith('/') else specifikator_url
                kodifikator_url = self.BASE_URL + kodifikator_url if kodifikator_url and kodifikator_url.startswith('/') else kodifikator_url
                
                return {
                    'subject': subject_code,
                    'year': year,
                    'demoversion': demoversion_url,
                    'specifikator': specifikator_url,
                    'kodifikator': kodifikator_url
                }
        
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке демоверсии {subject_code}: {e}")
            return None
    
    async def download_all_demoversii(self, years: List[int] = None) -> List[Dict]:
        """Скачивает демоверсии для всех предметов"""
        if not years:
            years = [2020, 2021, 2022, 2023, 2024, 2025]
        
        all_tasks = []
        
        async with self:
            for year in years:
                logger.info(f"📥 Загрузка демоверсий за {year} год...")
                
                # ЕГЭ
                for subject in self.SUBJECTS_EGE.keys():
                    demo = await self.download_demoversion(subject, year)
                    if demo:
                        all_tasks.append(demo)
                        await asyncio.sleep(1)
                
                # ОГЭ
                for subject in self.SUBJECTS_OGE.keys():
                    demo = await self.download_demoversion(subject, year)
                    if demo:
                        all_tasks.append(demo)
                        await asyncio.sleep(1)
        
        return all_tasks
    
    async def parse_pdf_tasks(self, pdf_url: str, subject_code: str) -> List[Dict]:
        """
        Парсит PDF с заданиями (требует pdfplumber)
        Это заготовка - нужно адаптировать под структуру ФИПИ
        """
        import pdfplumber
        import io
        
        tasks = []
        
        try:
            async with self.session.get(pdf_url) as response:
                if response.status != 200:
                    return tasks
                
                pdf_content = await response.read()
                
                with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                    current_task = {}
                    for page in pdf.pages:
                        text = page.extract_text()
                        # Здесь нужна логика парсинга конкретной структуры PDF
                        # ФИПИ имеет стандартный формат, который можно распарсить
        
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга PDF {pdf_url}: {e}")
        
        return tasks
