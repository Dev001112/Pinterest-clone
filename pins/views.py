# pins/views.py
from django.shortcuts import render, redirect
from .models import Pin
from .forms import PinForm

def index(request):
    pins = Pin.objects.order_by('-uploaded_at')
    return render(request, 'pins/index.html', {'pins': pins})

def upload_pin(request):
    if request.method == 'POST':
        form = PinForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PinForm()
    return render(request, 'pins/upload.html', {'form': form})
