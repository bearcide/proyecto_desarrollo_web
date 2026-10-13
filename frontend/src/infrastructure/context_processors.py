from django.conf import settings
from django.urls import reverse


def app_config(request):
    """Configuración pública para el JS (se serializa con json_script en base.html).

    El token de desarrollo SOLO se emite con DEBUG=True y mientras no haya API_LOGIN_PATH.
    """
    simulado = settings.DEBUG and not settings.API_LOGIN_PATH
    return {'app_config': {
        'apiBaseUrl': settings.API_BASE_URL,
        'authScheme': 'Bearer',
        'devToken': settings.API_DEV_TOKEN if simulado else '',
        'simulatedAuth': simulado,
        'loginPath': settings.API_LOGIN_PATH,
        'tenantId': settings.API_TENANT_ID,
        'withCredentials': settings.API_WITH_CREDENTIALS,
        'urls': {
            'login': reverse('login'),
            'dashboard': reverse('dashboard'),
            'inscripcion': reverse('inscripcion'),
            'horario': reverse('horario'),
        },
    }}
