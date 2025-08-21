from django.db import models
from django.utils.text import slugify

# Create your models here.
class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    class Meta:
        ordering = ['order', 'name']
        
        verbose_name = 'Категория услуги'
        verbose_name_plural = 'Категории услуг'
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        

class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, related_name='services', on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_min = models.PositiveIntegerField(help_text="Duration in minutes")
    buffer_after_min = models.PositiveIntegerField(
        default=0, help_text="Перерыв после услуги (мин)"
    )
    
    class Meta:
        ordering = ['category__order', 'name']
        
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class ServiceImage(models.Model):
    service = models.ForeignKey(Service, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='service_images/')
    
    class Meta:        
        verbose_name = 'Изображение услуги'
        verbose_name_plural = 'Изображения услуг'
        
    def __str__(self):
        return f"Картинка для {self.service.name}"