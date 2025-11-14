# pins/admin.py
from django.contrib import admin
from .models import Pin

@admin.register(Pin)
class PinAdmin(admin.ModelAdmin):
    list_display = ('id','caption','uploaded_at')
