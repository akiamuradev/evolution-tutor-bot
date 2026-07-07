import re
import logging
from typing import Tuple

logging.basicConfig(filename='blocked_requests.log', level=logging.INFO,
                    format='%(asctime)s - TG_ID:%(message)s')

EXTREMIST_KW = ["экстремизм", "террор", "взрыв", "оружие", "наркотик", "убей", "взорви"]
DEEPFAKE_KW = ["дипфейк", "deepfake", "подделай лицо", "озвучь голос", "клон голоса"]
COPYRIGHT_KW = ["netflix", "disney", "marvel", "pixar", "harry potter", "genshin"]

def check_safety(text: str, tg_id: int) -> Tuple[bool, str]:
    t = text.lower()
    if any(k in t for k in EXTREMIST_KW):
        logging.info(f"BLOCKED_EXT: {tg_id} | {text[:50]}")
        return False, "🚫 Запрос заблокирован. Экстремизм/терроризм запрещён ФЗ №114/ФЗ №35."
    if any(k in t for k in DEEPFAKE_KW):
        logging.info(f"BLOCKED_DF: {tg_id} | {text[:50]}")
        return False, " Запрос заблокирован. Дипфейки нарушают ст. 152.1 ГК РФ."
    if any(k in t for k in COPYRIGHT_KW):
        logging.info(f"BLOCKED_CP: {tg_id} | {text[:50]}")
        return False, "🚫 Запрос заблокирован. Контент по защищённым франшизам требует лицензии."
    if re.search(r"(сгенерируй|нарисуй|озвучь)\s+.*(фото|изображение|голос)\s+([а-яё]+)", t):
        return False, "🚫 Генерация изображений/голоса реальных лиц без согласия запрещена."
    return True, ""