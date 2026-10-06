class DomainException(Exception):
    """Excepción base para todos los errores del dominio."""
    pass


class EstudianteInvalidoException(DomainException):
    """Se lanza cuando un estudiante no cumple las reglas del negocio."""
    pass


class NumeroInscripcionInvalidoException(EstudianteInvalidoException):
    """El número de inscripción no es válido o está fuera de rango."""
    pass


class NumeroCuentaInvalidoException(EstudianteInvalidoException):
    """El número de cuenta no es válido."""
    pass


class CorreoInvalidoException(EstudianteInvalidoException):
    """El correo no tiene un formato válido."""
    pass