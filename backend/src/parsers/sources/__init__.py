"""Источники данных для парсинга"""
from .fipi_official import FIPIOfficialParser
from .sdamgia import SdamgiaParser
from .math100 import Math100Parser
from .yandex_repetitor import YandexRepetitorParser

__all__ = [
    'FIPIOfficialParser',
    'SdamgiaParser', 
    'Math100Parser',
    'YandexRepetitorParser'
]
