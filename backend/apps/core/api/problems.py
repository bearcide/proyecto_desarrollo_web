"""Problem Details de la API; invalid_params es una extensión del contrato."""
import logging
from http import HTTPStatus

from django.http import JsonResponse
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler, set_rollback

from apps.core.services.identidad import ErrorIdentidad
from apps.core.services.importacion_csv import ErrorImportacion

logger = logging.getLogger(__name__)


def parametros_invalidos(value, prefix=''):
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.extend(parametros_invalidos(child, f'{prefix}.{key}' if prefix else str(key)))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            path = f'{prefix}.{index}' if isinstance(child, (dict, list, tuple)) else prefix
            result.extend(parametros_invalidos(child, path))
    else:
        result.append({'name': prefix or 'non_field_errors', 'reason': str(value)})
    return result


def documento(status, code, detail, path, invalid_params=None):
    data = {
        'type': 'urn:inscripcionmadeeasy:problem:' + code.replace('_', '-'),
        'title': HTTPStatus(status).phrase,
        'status': status, 'detail': detail, 'instance': path, 'code': code,
    }
    if invalid_params is not None:
        data['invalid_params'] = invalid_params
    return data


def problem_exception_handler(exc, context):
    request = context.get('request')
    path = request.path if request else ''
    if isinstance(exc, ErrorImportacion):
        response = Response(status=400)
        code, detail = 'csv_invalid', str(exc)
    elif isinstance(exc, ErrorIdentidad):
        response = Response(status=exc.status)
        code, detail = exc.code, exc.detail
    else:
        response = exception_handler(exc, context)
        if response is None:
            set_rollback()
            logger.error('Error no controlado en API', exc_info=True)
            response = Response(status=500)
            code, detail = 'internal_error', 'Ocurrió un error interno.'
        else:
            codes = {400: 'validation_error', 401: 'authentication_failed',
                     403: 'permission_denied', 404: 'not_found', 405: 'method_not_allowed',
                     406: 'not_acceptable', 409: 'conflict', 415: 'unsupported_media_type',
                     429: 'throttled'}
            code = codes.get(response.status_code, 'api_error')
            detail = str(response.data.get('detail', 'La solicitud no es válida.')) if isinstance(response.data, dict) else 'La solicitud no es válida.'
    invalid = parametros_invalidos(getattr(exc, 'detail', {})) if isinstance(exc, ValidationError) else None
    response.data = documento(response.status_code, code, detail, path, invalid)
    if isinstance(exc, ErrorImportacion):
        response.data.update(exc.informe)
        response.data['invalid_params'] = [
            {'name': f"{e['archivo']}.{e['fila']}.{e['campo']}", 'reason': e['mensaje']}
            for e in exc.informe['errores']
        ]
    response.content_type = 'application/problem+json'
    response['Cache-Control'] = 'no-store'
    return response


class ApiProblemMiddleware:
    """Normaliza errores de resolución de URLs fuera de las vistas DRF."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/api/v1/') and response.status_code >= 400 and response.get('Content-Type', '').split(';')[0] != 'application/problem+json':
            status = response.status_code
            code = {404: 'not_found', 403: 'permission_denied', 400: 'validation_error'}.get(status, 'api_error')
            replacement = JsonResponse(documento(status, code, HTTPStatus(status).phrase, request.path), status=status, content_type='application/problem+json')
            for header, value in response.items():
                if header.lower() not in ('content-type', 'content-length'):
                    replacement[header] = value
            replacement['Cache-Control'] = 'no-store'
            return replacement
        return response
