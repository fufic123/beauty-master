from datetime import timedelta

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from celery import current_app

from booking.models import Booking
from notifications.models import OutboxEvent
from notifications.tasks import (
    send_outbox_event,
    register_outbox_event,
)


def _payload_base(b: Booking) -> dict:
    return {
        "service_id": b.service_id,
        "service_name": b.service.name if b.service_id else None,
        "customer_name": b.customer_name,
        "customer_email": b.customer_email,
        "customer_phone": b.customer_phone,
        "starts_at": b.starts_at.isoformat() if b.starts_at else None,
        "ends_at": b.ends_at.isoformat() if b.ends_at else None,
        "duration_minutes": b.service.duration_min,
        "date": b.date.isoformat() if b.date else None,
        "language": b.language,
    }


@receiver(post_save, sender=Booking)
def booking_created_outbox(sender, instance: Booking, **kwargs):
    if instance.status == Booking.Status.CONFIRMED:
        now = timezone.now()
        local_today = timezone.localdate()

        master_notify = OutboxEvent.objects.create(
            event_type="master_notify",
            execute_at=now,
            payload={
                **_payload_base(instance),
                "reason": f"booking_{instance.status.lower()}",
            },
            booking_id=instance.id,
        )
        send_outbox_event.delay(master_notify.id)
        
        client_notify = OutboxEvent.objects.create(
            event_type="client_notify",
            execute_at=now,
            payload={
                **_payload_base(instance),
                "reason": f"booking_{instance.status.lower()}",
            },
            booking_id=instance.id,
        )
        send_outbox_event.delay(client_notify.id)


        remind_at = instance.starts_at - timedelta(hours=1)

        client_reminder = OutboxEvent.objects.create(
            event_type="client_reminder",
            execute_at=remind_at,
            payload={
                **_payload_base(instance),
                "reason": "booking_confirmed",
                "reminder_offset_minutes": 60, # на час раньше
            },
            booking_id=instance.id,
        )

        if remind_at.date() == local_today and remind_at > now:
            register_outbox_event.delay(client_reminder.id)
        # иначе ничего не делаем: ночной beat сам найдёт и зарегистрирует


@receiver(post_save, sender=Booking)
def cancel_outbox_on_booking_cancel(sender, instance: Booking, **kwargs):
    if instance.status == Booking.Status.CANCELLED:
        events = OutboxEvent.objects.filter(
            booking_id=instance.id,
            processed=False
        )
        for ev in events:
            if ev.task_id:
                current_app.control.revoke(ev.task_id, terminate=True)
            ev.delete()
            

@receiver(post_delete, sender=Booking)
def delete_outbox_events_on_booking_delete(sender, instance: Booking, **kwargs):
    if instance.id:
        deleted, _ = OutboxEvent.objects.filter(booking_id=instance.id).delete()
        if deleted:
            print(f"[Outbox cleanup] Deleted {deleted} events for booking {instance.id}")