"""Vistas del frontend: solo entregan el HTML. Los datos los trae el JS desde la API REST
(ver static/js/api.js). Aquí no hay lógica de negocio ni datos de ejemplo."""
from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


def login_view(request):
    return render(request, 'login.html')


def dashboard(request):
    return render(request, 'dashboard.html')


def inscripcion(request):
    return render(request, 'inscripcion.html')


def horario(request):
    return render(request, 'horario.html')
