import json
from aiogram.types import URLInputFile
from config import MESSAGES_FILE, LOGO_URL, EVENT_DATE

def load_messages(lang: str = 'ru') -> dict:
    with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get(lang, {})

def get_logo() -> URLInputFile:
    return URLInputFile(LOGO_URL)

def get_event_date():
    return EVENT_DATE