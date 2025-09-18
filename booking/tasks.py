from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from booking.models import Booking


@shared_task
def clean_old_pending_bookings():
    now = timezone.now()
    timeout = timedelta(minutes=settings.LOCK_TIMEOUT)

    qs = Booking.objects.filter(
        status=Booking.Status.PENDING,
        created_at__lt=now - timeout,
    )
    count = qs.count()
    qs.delete()

    return f"Deleted {count} old pending bookings"
