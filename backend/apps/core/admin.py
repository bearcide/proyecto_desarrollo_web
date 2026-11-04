from django.contrib import admin
from .models import Tenant, PlanEstudios, Nodo, Prerrequisito, Alumno, NodoEstadistico

admin.site.register(Tenant)
admin.site.register(PlanEstudios)
admin.site.register(Nodo)
admin.site.register(Prerrequisito)
admin.site.register(Alumno)
admin.site.register(NodoEstadistico)