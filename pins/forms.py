# pins/forms.py
from django import forms
from .models import Pin

class PinForm(forms.ModelForm):
    class Meta:
        model = Pin
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Add a caption (optional)'})
        }
