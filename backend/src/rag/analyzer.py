"""Анализ трендов и прогнозирование заданий"""
import asyncpg
from typing import Dict, List
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """Анализирует тренды в заданиях ФИПИ"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
    
    async def get_exam_statistics(self, subject_code: str) -> Dict:
        """Общая статистика по предмету"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(DISTINCT year) as years_covered,
                    COUNT(DISTINCT topic) as unique_topics,
                    MIN(year) as earliest_year,
                    MAX(year) as latest_year
                FROM fipi_tasks t
                JOIN subjects s ON t.subject_id = s.id
                WHERE s.code = $1
            """, subject_code)
            
            return dict(stats) if stats else {}
    
    async def generate_prediction_report(self, subject_code: str) -> str:
        """Генерирует текстовый отчёт с прогнозом"""
        stats = await self.get_exam_statistics(subject_code)
        
        if not stats or stats.get('total_tasks', 0) == 0:
            return f"🔮 База заданий для {subject_code} пока пуста.\n\nЗагрузка данных в процессе..."
        
        report = f"🔮 АНАЛИЗ ТРЕНДОВ {subject_code.upper()}\n\n"
        report += f"📊 Всего проанализировано задач: {stats.get('total_tasks', 0)}\n"
        report += f"📅 Период: {stats.get('earliest_year', 'N/A')} - {stats.get('latest_year', 'N/A')}\n"
        report += f"📚 Уникальных тем: {stats.get('unique_topics', 0)}\n\n"
        
        report += "💡 Скоро здесь появится подробный анализ трендов и прогноз тем на экзамен!"
        
        return report
