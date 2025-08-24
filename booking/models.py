from django.db import models
from django.utils import timezone
from django.db.models import Q, F

# Create your models here.
class TimeOff(models.Model):
    date = models.DateField(unique=True)
    start = models.TimeField(blank=True, null=True)
    end = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-date', 'start']
        
        constraints = [
            models.CheckConstraint(check=Q(end__gt=F("start")), name="timeoff_end_after_start"),
        ]

        
        verbose_name = 'Выходной день'
        verbose_name_plural = 'Выходные дни'
        
    def __str__(self):
        return f"Выходной: {self.date} - {self.reason if self.reason else 'Без причины'}"
    

class DaysOff(models.Model):
    start = models.DateField(unique=True)
    end = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-start', 'end']
        
        constraints = [
            models.CheckConstraint(check=Q(end__gt=F("start")), name="daysoff_end_after_start"),
        ]

        
        verbose_name = 'Выходной день'
        verbose_name_plural = 'Выходные дни'
        
    def __str__(self):
        return f"Выходные с: {self.start} По {self.end} - {self.reason if self.reason else 'Без причины'}"
    

class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING    = "PENDING", "Pending"
        CONFIRMED  = "CONFIRMED", "Confirmed"
        COMPLETED  = "COMPLETED", "Completed"
        CANCELLED  = "CANCELLED", "Cancelled"
        NO_SHOW    = "NO_SHOW", "No show"

    customer_name  = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)

    service   = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="appointments")
    date = models.DateField()
    starts_at = models.DateTimeField()
    ends_at   = models.DateTimeField()
    status    = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    notes     = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-date', 'starts_at']
        
        constraints = [
            models.CheckConstraint(check=Q(ends_at__gt=F("starts_at")), name="appt_ends_after_starts"),
            models.UniqueConstraint(fields=["starts_at"], name="uniq_start_single_master"),
        ]
        
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        
    def __str__(self):
        return f"Бронирование: {self.customer_name} - {self.service.name} on {self.date} at {self.start_time}"