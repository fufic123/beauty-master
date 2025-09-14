import requests
from typing import Optional

from django.conf import settings
from django.template.loader import render_to_string


class TelegramServiceError(RuntimeError):
    pass


def send_telegram_message(
    template_base: str,  # шаблон сообщения без расширения
    context: dict,
) -> None:
    
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)   
    if not bot_token or not chat_id:
        raise TelegramServiceError("Telegram bot token or chat ID is not configured.")
    
    text = render_to_string(f"telegram/{template_base}.html", context).strip()

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"


    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

    if not resp.ok:
        raise TelegramServiceError(f"Telegram API error {resp.status_code}: {resp.text}")
    # если ответ не 2xx — поднимаем исключение (Celery сможет ретраить)