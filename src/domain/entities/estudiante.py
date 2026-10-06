from dataclasses import dataclass, field
from typing import Optional

from src.domain.value_objects.numero_inscripcion import NumeroInscripcion
from src.domain.value_objects.numero_cuenta import NumeroCuenta
from src.domain.value_objects.correo import Correo
from src.domain.exceptions.domain_exceptions import EstudianteInvalidoException


@dataclass
class Estudiante:
    """
    Entidad que representa a un estudiante en el sistema de inscripción.

    Reglas de negocio:
    - El número de cuenta es único y actúa como identificador.
    - El número de inscripción es único y define el orden de inscripción.
    - El correo principal es obligatorio; el de respaldo es opcional.
    """
    numero_cuenta: NumeroCuenta
    numero_inscripcion: NumeroInscripcion
    nombre: str
    apellido_paterno: str
    apellido_materno: str
    correo: Correo
    correo_respaldo: Optional[Correo] = None

    def __post_init__(self):
        self._validar_nombre(self.nombre, "nombre")
        self._validar_nombre(self.apellido_paterno, "apellido paterno")
        self._validar_nombre(self.apellido_materno, "apellido materno")

    @staticmethod
    def _validar_nombre(valor: str, campo: str) -> None:
        if not isinstance(valor, str):
            raise EstudianteInvalidoException(
                f"El {campo} debe ser una cadena de texto."
            )
        if not valor.strip():
            raise EstudianteInvalidoException(
                f"El {campo} no puede estar vacío."
            )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.numero_cuenta})"