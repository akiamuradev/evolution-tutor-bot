"""
Универсальный загрузчик для всех предметов
Агрегирует данные из всех источников
"""
import asyncio
from typing import List, Dict
import logging
from .sources.fipi_official import FIPIOfficialParser
from .sources.sdamgia import SdamgiaParser
from .sources.math100 import Math100Parser

logger = logging.getLogger(__name__)

class UniversalLoader:
    """Универсальный загрузчик заданий для всех предметов"""
    
    ALL_SUBJECTS = [
        # ЕГЭ
        ('math-profile', 'Математика (профиль)'),
        ('russian', 'Русский язык (ЕГЭ)'),
        ('physics', 'Физика'),
        ('chemistry', 'Химия'),
        ('biology', 'Биология'),
        ('history', 'История'),
        ('social-studies', 'Обществознание'),
        ('informatics', 'Информатика'),
        ('geography', 'География'),
        ('literature', 'Литература'),
        ('english', 'Английский язык'),
        # ОГЭ
        ('math-base', 'Математика (база/ОГЭ)'),
        ('russian-oge', 'Русский язык (ОГЭ)'),
        ('physics-oge', 'Физика (ОГЭ)'),
        ('chemistry-oge', 'Химия (ОГЭ)'),
        ('biology-oge', 'Биология (ОГЭ)'),
        ('history-oge', 'История (ОГЭ)'),
        ('social-studies-oge', 'Обществознание (ОГЭ)'),
        ('informatics-oge', 'Информатика (ОГЭ)'),
        ('geography-oge', 'География (ОГЭ)'),
        ('literature-oge', 'Литература (ОГЭ)'),
        ('english-oge', 'Английский язык (ОГЭ)'),
    ]
    
    def __init__(self, task_loader):
        self.task_loader = task_loader
        self.stats = {
            'total_downloaded': 0,
            'by_subject': {},
            'by_source': {}
        }
    
    async def download_all_subjects(self, sources: List[str] = None):
        """
        Скачивает задания для всех предметов
        
        sources: список источников ['fipi', 'sdamgia', 'math100']
        """
        if not sources:
            sources = ['sdamgia', 'math100', 'fipi']
        
        logger.info("🚀 Начинаю загрузку заданий для всех предметов...")
        
        for subject_code, subject_name in self.ALL_SUBJECTS:
            logger.info(f"\n📚 {subject_name} ({subject_code})")
            
            tasks = []
            
            # Math100 для математики
            if 'math' in subject_code and 'math100' in sources:
                logger.info("  📥 Загрузка с Math100.ru...")
                try:
                    async with Math100Parser() as parser:
                        math_tasks = await parser.parse_all_tasks(subject_code)
                        tasks.extend(math_tasks)
                        self.stats['by_source']['math100'] = self.stats['by_source'].get('math100', 0) + len(math_tasks)
                except Exception as e:
                    logger.error(f"  ❌ Ошибка Math100: {e}")
            
            # Sdamgia для всех предметов
            if 'sdamgia' in sources:
                logger.info("  📥 Загрузка с Sdamgia.ru...")
                try:
                    async with SdamgiaParser() as parser:
                        sdamgia_tasks = await parser.parse_subject_tasks(subject_code, limit=100)
                        tasks.extend(sdamgia_tasks)
                        self.stats['by_source']['sdamgia'] = self.stats['by_source'].get('sdamgia', 0) + len(sdamgia_tasks)
                except Exception as e:
                    logger.error(f"  ❌ Ошибка Sdamgia: {e}")
            
            # ФИПИ (демоверсии)
            if 'fipi' in sources:
                logger.info("  📥 Загрузка с FIPI.ru...")
                try:
                    async with FIPIOfficialParser() as parser:
                        fipi_demos = await parser.download_demoversion(subject_code, 2025)
                        if fipi_demos:
                            tasks.append({
                                'subject_code': subject_code,
                                'year': 2025,
                                'task_number': 0,
                                'difficulty': 'demo',
                                'topic': 'Демоверсия',
                                'condition': f"Демоверсия: {fipi_demos}",
                                'solution': '',
                                'answer': '',
                                'source_url': fipi_demos.get('demoversion', '')
                            })
                            self.stats['by_source']['fipi'] = self.stats['by_source'].get('fipi', 0) + 1
                except Exception as e:
                    logger.error(f"  ❌ Ошибка FIPI: {e}")
            
            # Загружаем в БД
            if tasks:
                logger.info(f"  💾 Загрузка {len(tasks)} задач в базу данных...")
                await self.task_loader.load_tasks(tasks)
                self.stats['total_downloaded'] += len(tasks)
                self.stats['by_subject'][subject_code] = len(tasks)
            
            await asyncio.sleep(2)  # Пауза между предметами
        
        logger.info(f"\n✅ Загрузка завершена!")
        logger.info(f"📊 Всего загружено: {self.stats['total_downloaded']} задач")
        logger.info(f"📈 По источникам: {self.stats['by_source']}")
        logger.info(f"📈 По предметам: {self.stats['by_subject']}")
        
        return self.stats
