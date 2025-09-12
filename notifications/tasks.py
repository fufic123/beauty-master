from celery import shared_task
from django.utils import timezone
from .models import OutboxEvent

@shared_task
def schedule_outbox_event(event_type: str, payload: dict, execute_at: timezone.datetime = None):
    if execute_at is None:
        execute_at = timezone.now()
    event = OutboxEvent.objects.create(
        event_type=event_type,
        payload=payload,
        execute_at=execute_at,
    )
    return event


@shared_task(name="notifications.tasks.send_outbox_event")
def send_outbox_event(outbox_id: int):
    event = OutboxEvent.objects.get(id=outbox_id)
    print("=== SEND NOW ===")
    print(f"[{timezone.now()}] OutboxEvent ID: {event.id}")
    print(f"Type: {event.event_type}")
    print(f"Execute at: {event.execute_at}")
    print(f"Payload: {event.payload}")
    print("================")
    return {"id": event.id, "payload": event.payload, "execute_at": str(event.execute_at)}


@shared_task(name="notifications.tasks.register_outbox_event")
def register_outbox_event(outbox_id: int):
    
    event = OutboxEvent.objects.get(id=outbox_id)
    eta = event.execute_at
    print("=== REGISTER WITH ETA ===")
    print(f"[{timezone.now()}] OutboxEvent ID: {event.id}")
    print(f"Will execute at: {eta}")
    print(f"Payload: {event.payload}")
    print("=========================")

    # планируем фактическую отправку
    send_outbox_event.apply_async(args=[event.id], eta=eta)
    return {"id": event.id, "eta": str(eta)}