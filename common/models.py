from django.db import models
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True
        ordering = ['-created_at']
        verbose_name = "Base Model"
        verbose_name_plural = "Base Models"