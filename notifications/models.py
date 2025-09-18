from django.db import models
from django.utils import timezone


class OutboxEvent(models.Model):
    class EventTypes(models.TextChoices):
        MASTER_NOTIFY = "master_notify", "Notify Master" 
        CLIENT_NOTIFY = "client_notify", "Client Notify"
        CLIENT_REMINDER = "client_reminder", "Client Reminder"

    
    event_type = models.CharField(
        max_length=50,
        choices=EventTypes.choices,
    )
    payload = models.JSONField()
    execute_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    booking_id = models.IntegerField(null=True, db_index=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=["processed", "execute_at"]),
            models.Index(fields=["booking_id"]),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} at {self.execute_at} (processed={self.processed})"
