from django.contrib import admin
from django.utils.html import format_html
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import ServiceCategory, Service, ServiceImage

# Register your models here.
class Max10ImagesInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False):
                if form.cleaned_data.get("image"):
                    total += 1
        # учитываем уже существующие + новые
        existing = self.instance.images.count() if self.instance.pk else 0
        if existing + total > 10:
            raise ValidationError("Максимум 10 изображений на услугу.")

class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    formset = Max10ImagesInlineFormSet
    extra = 3
    min_num = 0
    can_delete = True
    fields = ("preview", "image",)
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px" />', obj.image.url)
        return "—"

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "slug", "image")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "duration_min", "price", "slug",)
    list_filter = ("category",)
    search_fields = ("name", "category__name",)
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    inlines = [ServiceImageInline]
