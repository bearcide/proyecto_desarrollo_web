"""Puerto para un PAC autorizado: sin timbrado ni UUID fiscales simulados."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentoFiscal:
    uuid_fiscal: str
    xml: bytes
    pdf: bytes
    proveedor: str


class ProveedorFiscal(ABC):
    @abstractmethod
    def emitir(self, solicitud, clave_idempotencia: str) -> DocumentoFiscal:
        """Validar datos CFDI 4.0 y timbrar exclusivamente con un PAC autorizado."""
        raise NotImplementedError

    @abstractmethod
    def consultar(self, referencia: str) -> DocumentoFiscal:
        raise NotImplementedError


class FiscalNoConfigurado(ProveedorFiscal):
    def emitir(self, solicitud, clave_idempotencia):
        raise NotImplementedError('PAC no configurado; el comprobante interno no es CFDI.')

    def consultar(self, referencia):
        raise NotImplementedError('PAC no configurado.')
