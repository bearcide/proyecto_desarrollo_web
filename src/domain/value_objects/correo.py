import re
from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import CorreoInvalidoException


# Expresión regular simple para validar correos.
# No es perfecta (ninguna lo es), pero cubre el 99% de casos reales.
PATRON_CORREO = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class Correo:
    """
    Value Object que representa un correo electrónico válido.
    """
    direccion: str

    def __post_init__(self):
        if not isinstance(self.direccion, str):
            raise CorreoInvalidoException("El correo debe ser una cadena de texto.")
        correo_limpio = self.direccion.strip().lower()
        if not PATRON_CORREO.match(correo_limpio):
            raise CorreoInvalidoException(
                f"El correo '{self.direccion}' no tiene un formato válido."
            )
        # Como el dataclass es frozen, usamos object.__setattr__ para normalizar
        object.__setattr__(self, "direccion", correo_limpio)

    def __str__(self) -> str:
        return self.direccion