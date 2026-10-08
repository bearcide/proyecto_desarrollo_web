"""Datos de ejemplo para el frontend.

TODO: reemplazar por llamadas a la capa de servicios cuando exista el backend.
"""

DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

ESTUDIANTE = {
    'nombre': 'Ana Martínez López',
    'matricula': '20260123',
    'carrera': 'Ingeniería en Sistemas',
    'semestre': 5,
    'numero_inscripcion': 142,
    'ventana_inicio': '2026-10-12T09:00:00',
    'ventana_texto': 'Lunes 12 de octubre, 9:00 a. m.',
    'materias_aprobadas': ['Cálculo I', 'Álgebra', 'Programación I'],
}

MATERIAS = [
    {'id': 1, 'clave': 'MAT201', 'nombre': 'Cálculo II', 'profesor': 'Dr. Ramírez',
     'creditos': 8, 'cupo': 30, 'inscritos': 22, 'requisitos': ['Cálculo I'],
     'horarios': [{'dia': 'Lunes', 'ini': 8, 'fin': 10}, {'dia': 'Miércoles', 'ini': 8, 'fin': 10}]},
    {'id': 2, 'clave': 'SIS210', 'nombre': 'Estructuras de Datos', 'profesor': 'Mtra. Salinas',
     'creditos': 8, 'cupo': 30, 'inscritos': 29, 'requisitos': ['Programación I'],
     'horarios': [{'dia': 'Martes', 'ini': 10, 'fin': 12}, {'dia': 'Jueves', 'ini': 10, 'fin': 12}]},
    {'id': 3, 'clave': 'SIS220', 'nombre': 'Bases de Datos', 'profesor': 'Ing. Torres',
     'creditos': 6, 'cupo': 25, 'inscritos': 25, 'requisitos': ['Programación I'],
     'horarios': [{'dia': 'Lunes', 'ini': 10, 'fin': 12}, {'dia': 'Viernes', 'ini': 10, 'fin': 12}]},
    {'id': 4, 'clave': 'MAT230', 'nombre': 'Álgebra Lineal', 'profesor': 'Dra. Herrera',
     'creditos': 6, 'cupo': 35, 'inscritos': 18, 'requisitos': ['Álgebra'],
     'horarios': [{'dia': 'Lunes', 'ini': 9, 'fin': 11}, {'dia': 'Jueves', 'ini': 8, 'fin': 10}]},
    {'id': 5, 'clave': 'SIS240', 'nombre': 'Desarrollo Web', 'profesor': 'Mtro. Aguilar',
     'creditos': 6, 'cupo': 30, 'inscritos': 12, 'requisitos': ['Programación I'],
     'horarios': [{'dia': 'Miércoles', 'ini': 12, 'fin': 14}, {'dia': 'Viernes', 'ini': 12, 'fin': 14}]},
    {'id': 6, 'clave': 'SIS250', 'nombre': 'Ingeniería de Software', 'profesor': 'Mtra. García',
     'creditos': 8, 'cupo': 30, 'inscritos': 27, 'requisitos': ['Estructuras de Datos'],
     'horarios': [{'dia': 'Martes', 'ini': 12, 'fin': 14}, {'dia': 'Jueves', 'ini': 12, 'fin': 14}]},
]

# IDs de materias ya inscritas (ejemplo)
INSCRITAS_IDS = [5]


def horario_semanal(materias, horas=range(8, 14)):
    """Arma una tabla horas x días para renderizar sin JS."""
    filas = []
    for h in horas:
        celdas = []
        for dia in DIAS:
            celda = None
            for m in materias:
                for b in m['horarios']:
                    if b['dia'] == dia and b['ini'] <= h < b['fin']:
                        celda = m
            celdas.append(celda)
        filas.append({'hora': f'{h}:00 – {h + 1}:00', 'celdas': celdas})
    return filas
