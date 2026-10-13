from rest_framework.permissions import BasePermission


class TieneTenant(BasePermission):
    """Exige un usuario autenticado asociado a una escuela (request.user.tenant).

    Sin tenant no hay forma de aislar datos, así que se niega el acceso completo.
    """

    message = 'Tu usuario no está asociado a ninguna escuela.'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and getattr(user, 'tenant', None) is not None
        )
