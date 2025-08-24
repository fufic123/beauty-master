from django.contrib import admin
from .models import TimeOff, DaysOff, Booking

# Register your models here.
@admin.register(DaysOff)
class DaysOffAdmin(admin.ModelAdmin):
    list_display = ("start", "end", "reason")
    search_fields = ("reason",)
    
@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ("date", "start", "end", "reason")
    list_filter = ("date",)
    search_fields = ("reason",)

@admin.register(Booking)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("starts_at", "ends_at", "service", "customer_name", "customer_phone", "status", "created_at")
    list_filter = ("status", "service")
    search_fields = ("customer_name", "customer_phone", "customer_email", "notes")
    readonly_fields = ("created_at",)