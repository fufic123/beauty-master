from django.db import models
from django.utils import timezone


class OutboxEvent(models.Model):
    class EventTypes(models.TextChoices):
        MASTER_NOTIFY = "master_notify", "Notify Master"
        CLIENT_REMINDER = "client_reminder", "Client Reminder"
        CLIENT_NOTIFY = "client_notify", "Client Notify"

    
    event_type = models.CharField(
        max_length=50,
        choices=EventTypes.choices,
    )
    payload = models.JSONField()
    execute_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} at {self.execute_at} (processed={self.processed})"
