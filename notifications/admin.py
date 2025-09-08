from django.contrib import admin
from .models import OutboxEvent
from django.utils import timezone

# Register your models here.
@admin.register(OutboxEvent)
class OutboxEventAdmin(admin.ModelAdmin):
    list_display = (
        "id", "event_type", "execute_at", "processed", "processed_at", "short_payload"
    )
    list_filter = (
        "event_type", "processed",
        ("execute_at", admin.DateFieldListFilter),
        ("processed_at", admin.DateFieldListFilter),
    )
    search_fields = ("payload",)
    date_hierarchy = "execute_at"
    readonly_fields = ("processed_at",)
    
    @admin.display(description="payload")
    def short_payload(self, obj: OutboxEvent):
        # Ensure JSONField (dict) becomes a short string
        try:
            txt = obj.payload if isinstance(obj.payload, str) else json.dumps(obj.payload, ensure_ascii=False)
        except Exception:
            txt = str(obj.payload)
        return (txt[:80] + "…") if len(txt) > 80 else txt