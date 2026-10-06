from dataclasses import dataclass
from src.domain.exceptions.domain_exceptions import NumeroCuentaInvalidoException


@dataclass(frozen=True)
class NumeroCuenta:
    """
    Value Object que representa el número de cuenta único de un estudiante.
    Es la llave primaria del estudiante en el sistema.
    """
    valor: str

    def __post_init__(self):
        if not isinstance(self.valor, str):
            raise NumeroCuentaInvalidoException(
                "El número de cuenta debe ser una cadena de texto."
            )
        valor_limpio = self.valor.strip()
        if not valor_limpio:
            raise NumeroCuentaInvalidoException(
                "El número de cuenta no puede estar vacío."
            )
        if not valor_limpio.isdigit():
            raise NumeroCuentaInvalidoException(
                "El número de cuenta solo puede contener dígitos."
            )
        object.__setattr__(self, "valor", valor_limpio)

    def __str__(self) -> str:
        return self.valor