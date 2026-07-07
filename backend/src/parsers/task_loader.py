"""Загрузчик задач в базу данных с генерацией эмбеддингов"""
import asyncpg
import asyncio
from typing import List, Dict
import logging
import httpx

logger = logging.getLogger(__name__)

class TaskLoader:
    """Загружает задачи в PostgreSQL с векторными эмбеддингами"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool = None
    
    async def connect(self):
        """Подключение к БД"""
        self.pool = await asyncpg.create_pool(self.db_url)
        logger.info("✅ Подключено к базе данных")
    
    async def close(self):
        """Закрытие подключения"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Отключено от базы данных")
    
    async def get_subject_id(self, subject_code: str) -> int:
        """Получает ID предмета по коду"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM subjects WHERE code = $1",
                subject_code
            )
            if not row:
                raise ValueError(f"Предмет {subject_code} не найден в БД")
            return row['id']
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Генерирует векторный эмбеддинг для текста
        Используем OpenAI или локальную модель
        """
        # Вариант 1: OpenAI API (платно, но качественно)
        # api_key = os.getenv("OPENAI_API_KEY")
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.openai.com/v1/embeddings",
        #         headers={"Authorization": f"Bearer {api_key}"},
        #         json={"input": text, "model": "text-embedding-3-small"}
        #     )
        #     return response.json()["data"][0]["embedding"]
        
        # Вариант 2: Бесплатная альтернатива (например, через HuggingFace)
        # Или локальная модель sentence-transformers
        
        # Для начала можно использовать заглушку (но это не будет работать для поиска)
        logger.warning("⚠️ Генерация эмбеддингов не настроена, используем нулевой вектор")
        return [0.0] * 1536
    
    async def load_tasks(self, tasks: List[Dict], batch_size: int = 50):
        """
        Загружает задачи в БД пакетами
        tasks: список задач из парсера
        """
        total = len(tasks)
        loaded = 0
        
        for i in range(0, total, batch_size):
            batch = tasks[i:i + batch_size]
            
            async with self.pool.acquire() as conn:
                for task in batch:
                    try:
                        # Получаем ID предмета
                        subject_id = await self.get_subject_id(task['subject_code'])
                        
                        # Генерируем эмбеддинг из условия задачи
                        embedding_text = f"{task['condition']} {task['topic']}"
                        embedding = await self.generate_embedding(embedding_text)
                        
                        # Вставляем задачу
                        await conn.execute("""
                            INSERT INTO fipi_tasks (
                                subject_id, year, task_number, difficulty,
                                topic, subtopic, condition, solution, answer,
                                source_url, embedding
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            ON CONFLICT DO NOTHING
                        """, 
                            subject_id,
                            task.get('year'),
                            task.get('task_number'),
                            task.get('difficulty'),
                            task.get('topic'),
                            task.get('subtopic'),
                            task.get('condition'),
                            task.get('solution'),
                            task.get('answer'),
                            task.get('source_url'),
                            embedding
                        )
                        
                        loaded += 1
                        
                        if loaded % 100 == 0:
                            logger.info(f"📥 Загружено {loaded}/{total} задач")
                    
                    except Exception as e:
                        logger.error(f"❌ Ошибка загрузки задачи: {e}")
                        continue
            
            # Небольшая пауза между пакетами
            await asyncio.sleep(0.5)
        
        logger.info(f"✅ Загружено {loaded} из {total} задач")
    
    async def get_statistics(self) -> Dict:
        """Получает статистику загруженных задач"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT subject_id) as subjects,
                    COUNT(DISTINCT year) as years,
                    COUNT(DISTINCT topic) as topics
                FROM fipi_tasks
            """)
            return dict(stats)
