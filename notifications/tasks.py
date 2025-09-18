from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from .models import OutboxEvent
from .dispatcher import send_event

# для ретраев по сетевым/SMTP-ошибкам
import socket
from smtplib import SMTPException
from requests.exceptions import RequestException
from django.core.exceptions import ObjectDoesNotExist
from .services.telegram_service import TelegramServiceError


@shared_task(
    autoretry_for=(RequestException, SMTPException, socket.timeout, TimeoutError, RuntimeError, TelegramServiceError),
    retry_backoff=True,          # экспоненциально: 1s, 2s, 4s, ...
    retry_jitter=True,           # немного рандома к бэкоффу
    retry_kwargs={"max_retries": 5},
)
def send_outbox_event(outbox_id: int):
    with transaction.atomic():
        event = OutboxEvent.objects.select_for_update().get(id=outbox_id)
        if event.processed:
            return

        send_event(event.event_type, event.payload)

        event.processed = True
        event.processed_at = timezone.now()
        event.save(update_fields=["processed", "processed_at"])
    

@shared_task
def register_outbox_event(outbox_id: int):
    """
    Регистрирует отправку OutboxEvent на точное время execute_at (ETA).
    Если execute_at уже прошло — шлём сразу.
    """
    event = OutboxEvent.objects.get(id=outbox_id)
    now = timezone.now()
    if event.execute_at and event.execute_at > now:
        res = send_outbox_event.apply_async(args=[event.id], eta=event.execute_at)
        event.task_id = res.id
        event.save(update_fields=["task_id"])
    else:
        send_outbox_event.delay(event.id)


@shared_task(
    autoretry_for=(Exception,),  # на всякий случай: если что-то пошло не так во время планирования
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def schedule_outbox_event():
    """
    Ночной планировщик (дергается Celery Beat).
    Находит все непросессенные события на СЕГОДНЯ и:
      - если время прошло — шлёт сразу,
      - если в будущем — регистрирует с ETA.
    """
    today = timezone.localdate()
    now = timezone.now()

    qs = OutboxEvent.objects.filter(
        processed=False,
        execute_at__date=today,
    )

    scheduled = 0
    sent_now = 0

    # небольшой допуск назад на случай дрейфа часов/рестартов
    grace_past = now - timedelta(minutes=1)

    for ev in qs.iterator():
        if ev.execute_at <= grace_past:
            send_outbox_event.delay(ev.id)
            sent_now += 1
        else:
            send_outbox_event.apply_async(args=[ev.id], eta=ev.execute_at)
            scheduled += 1

    # лаконичный лог в воркере
    print(f"[schedule_outbox_event] {today} scheduled={scheduled} sent_now={sent_now} total={scheduled + sent_now}")

    return {"today": str(today), "scheduled": scheduled, "sent_now": sent_now}