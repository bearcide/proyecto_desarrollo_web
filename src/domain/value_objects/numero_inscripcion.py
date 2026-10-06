from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import NumeroInscripcionInvalidoException


@dataclass(frozen=True)
class NumeroInscripcion:
    """
    Value Object que representa el número de inscripción de un estudiante.
    Es único y va del 0 al N de alumnos registrados.
    """
    valor: int

    def __post_init__(self):
        if not isinstance(self.valor, int):
            raise NumeroInscripcionInvalidoException(
                "El número de inscripción debe ser un entero."
            )
        if self.valor < 0:
            raise NumeroInscripcionInvalidoException(
                "El número de inscripción no puede ser negativo."
            )

    def __str__(self) -> str:
        return str(self.valor)

    def __int__(self) -> int:
        return self.valor