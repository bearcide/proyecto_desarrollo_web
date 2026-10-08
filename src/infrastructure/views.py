from django.shortcuts import render, redirect

from .mock_data import (
    DIAS, ESTUDIANTE, MATERIAS, INSCRITAS_IDS, horario_semanal,
)


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        # TODO: autenticación real (django.contrib.auth)
        return redirect('dashboard')
    return render(request, 'login.html')


def dashboard(request):
    inscritas = [m for m in MATERIAS if m['id'] in INSCRITAS_IDS]
    return render(request, 'dashboard.html', {
        'estudiante': ESTUDIANTE,
        'inscritas': inscritas,
        'creditos': sum(m['creditos'] for m in inscritas),
    })


def inscripcion(request):
    return render(request, 'inscripcion.html', {
        'estudiante': ESTUDIANTE,
        'materias': MATERIAS,
        'inscritas_ids': INSCRITAS_IDS,
    })


def horario(request):
    inscritas = [m for m in MATERIAS if m['id'] in INSCRITAS_IDS]
    return render(request, 'horario.html', {
        'estudiante': ESTUDIANTE,
        'dias': DIAS,
        'filas': horario_semanal(inscritas),
        'inscritas': inscritas,
    })
