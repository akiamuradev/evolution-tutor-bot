"""Парсеры для загрузки заданий ФИПИ"""
from .fipi_parser import FIPIParser
from .task_loader import TaskLoader

__all__ = ['FIPIParser', 'TaskLoader']
