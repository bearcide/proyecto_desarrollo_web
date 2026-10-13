from rest_framework import status
from rest_framework.exceptions import APIException


class Conflict(APIException):
    """409: la operación choca con el estado actual de los datos."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'La operación entra en conflicto con los datos existentes.'
    default_code = 'conflict'
