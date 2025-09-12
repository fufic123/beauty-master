from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from booking.models import Booking
from notifications.models import OutboxEvent
from notifications.tasks import (
    send_outbox_event,
    register_outbox_event,
)


def _payload_base(b: Booking) -> dict:
    return {
        "booking_id": b.id,
        "service_id": b.service_id,
        "service_name": b.service.name if b.service_id else None,
        "customer_name": b.customer_name,
        "customer_email": b.customer_email,
        "customer_phone": b.customer_phone,
        "starts_at": b.starts_at.isoformat() if b.starts_at else None,
        "date": b.date.isoformat() if b.date else None,
        "language": b.language,
    }


@receiver(post_save, sender=Booking)
def booking_created_outbox(sender, instance: Booking, created: bool, **kwargs):
    if not created:
        return

    now = timezone.now()
    local_today = timezone.localdate()

    master_notify = OutboxEvent.objects.create(
        event_type="master_notify",
        execute_at=now,
        payload={
            **_payload_base(instance),
            "recipient": "master",
        },
    )
    send_outbox_event.delay(master_notify.id)
    
    client_notify = OutboxEvent.objects.create(
        event_type="client_notify",
        execute_at=now,
        payload={
            **_payload_base(instance),
            "recipient": "client",
        },
    )
    send_outbox_event.delay(client_notify.id)

    remind_at = instance.starts_at - timedelta(hours=1)

    client_reminder = OutboxEvent.objects.create(
        event_type="client_reminder",
        execute_at=remind_at,
        payload={
            **_payload_base(instance),
            "recipient": "client",
            "reminder_offset_minutes": 60, # на час раньше
        },
    )

    if remind_at.date() == local_today and remind_at > now:
        register_outbox_event.delay(client_reminder.id)
    # иначе ничего не делаем: ночной beat сам найдёт и зарегистрирует
