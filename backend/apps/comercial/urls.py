from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

router = DefaultRouter()
for prefijo,clase in [('planes',api.PlanView),('precios',api.PrecioView),('instituciones',api.InstitucionView),('contratos',api.ContratoView),('ordenes',api.OrdenView),('suscripciones',api.SuscripcionView),('licencias',api.LicenciaView),('transacciones',api.TransaccionView),('comprobantes',api.ComprobanteView),('facturas',api.FacturaView),('eventos',api.EventoView)]:
    router.register(prefijo,clase,basename='comercial-'+prefijo)
urlpatterns = [path('',include(router.urls)),path('checkout/',api.checkout),path('acceso/',api.acceso),path('demo/confirmar/',api.demo),path('ingresos/',api.ingresos),path('webhooks/stripe/',api.webhook)]
