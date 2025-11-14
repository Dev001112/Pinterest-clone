# pins/models.py
from django.db import models

class Pin(models.Model):
    image = models.ImageField(upload_to='pins/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Pin {self.pk}"
