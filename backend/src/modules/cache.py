"""Кэширование ответов ИИ для ускорения и экономии"""
import hashlib
import json
import time
from collections import OrderedDict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class LRUCache:
    """Least Recently Used cache с ограничением по размеру"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        max_size: максимальное количество записей
        ttl: время жизни записи в секундах (по умолчанию 1 час)
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_key(self, messages: list, model: str) -> str:
        """Генерирует уникальный ключ для запроса"""
        content = json.dumps(messages, sort_keys=True, ensure_ascii=False) + model
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, messages: list, model: str) -> Optional[str]:
        """Получает ответ из кэша"""
        key = self._generate_key(messages, model)
        
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        
        # Проверяем, не устарела ли запись
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            logger.info(f"🗑️ Кэш устарел: {key[:8]}")
            return None
        
        # Перемещаем в конец (последнее использование)
        self.cache.move_to_end(key)
        logger.info(f"✅ Кэш HIT: {key[:8]}")
        return value
    
    def set(self, messages: list, model: str, response: str):
        """Сохраняет ответ в кэш"""
        key = self._generate_key(messages, model)
        
        # Если кэш переполнен, удаляем самую старую запись
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.info(f"🗑️ Кэш переполнен, удалено: {oldest_key[:8]}")
        
        self.cache[key] = (response, time.time())
        logger.info(f"💾 Кэш SAVE: {key[:8]} ({len(self.cache)}/{self.max_size})")
    
    def clear(self):
        """Очищает кэш"""
        self.cache.clear()
        logger.info("🗑️ Кэш очищен")
    
    def stats(self) -> dict:
        """Статистика кэша"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }

# Глобальный кэш
ai_cache = LRUCache(max_size=1000, ttl=3600)  # 1000 записей, 1 час жизни
