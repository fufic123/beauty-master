from typing import Optional
from datetime import datetime

from django.conf import settings

from notifications.services.email_service import send_email_notification
from notifications.services.telegram_service import send_telegram_message


def _format_datetime(iso_str) -> Optional[str]:
    if not iso_str:
        return None
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%H:%M")

def send_event(event_type: str, payload: dict) -> None:
    context = payload.copy()
    context.update(
        {
            "starts_at": _format_datetime(payload.get("starts_at")),
            "ends_at": _format_datetime(payload.get("ends_at")),
        }
    )
    if event_type == "master_notify":        
        send_telegram_message(
            template_base=context.get("reason"),
            context=context,
        )
        
    elif event_type == "client_notify":        
        send_email_notification(
            template_base=context.get("reason"),
            context=context,
            to_email=context.get("customer_email"),
            language=context.get("language"),
        )
        
    elif event_type == "client_reminder":        
        send_email_notification(
            template_base=context.get("reason"),
            context=context,
            to_email=context.get("customer_email"),
            language=context.get("language"),
            event_type=event_type,
        )
        
    else:
        return

