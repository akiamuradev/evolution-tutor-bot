"""Модули бота ЭВО:ЛЮЦИЯ (только для школьников)"""
from .utils import force_clean_text, split_text_for_telegram, clean_markdown_for_document
from .ai_client import call_openrouter
from .cache import ai_cache
from .keyboards import (
    get_start_keyboard, get_grade_keyboard,
    get_main_menu_keyboard, get_doc_format_keyboard, get_subscribe_keyboard,
    get_exam_subjects_keyboard, get_settings_keyboard, get_parent_consent_keyboard,
    get_back_keyboard, get_practice_subjects_keyboard, get_task_keyboard
)
from .prompts import get_schoolboy_prompt, get_schoolboy_system_prompt, get_document_prompt

__all__ = [
    'force_clean_text', 'split_text_for_telegram', 'clean_markdown_for_document',
    'call_openrouter', 'ai_cache',
    'get_start_keyboard', 'get_grade_keyboard',
    'get_main_menu_keyboard', 'get_doc_format_keyboard', 'get_subscribe_keyboard',
    'get_exam_subjects_keyboard', 'get_settings_keyboard', 'get_parent_consent_keyboard',
    'get_back_keyboard', 'get_practice_subjects_keyboard', 'get_task_keyboard',
    'get_schoolboy_prompt', 'get_schoolboy_system_prompt', 'get_document_prompt'
]
