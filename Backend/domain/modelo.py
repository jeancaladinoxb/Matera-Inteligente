# PROVISIONAL (Julián, commit 0): simulación del contrato del dominio para poder desarrollar y probar
# los adaptadores mientras David implementa el dominio real. David puede reemplazar este archivo.
# Contrato: conservar nombres, campos y firmas. Sin lógica de negocio. Ver CONTRATOS.md.
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Ya existen en la fase 1: se re-exportan para que el contrato tenga un solo punto de importación.
from domain.entities import EvaluacionMatera, LecturaSensores, RangoEspecie  # noqa: F401
from domain.excepciones import AccesoDenegado
from domain.value_objects import EstadoParametro, IndiceVitalidad  # noqa: F401


# TODO(David): EvaluacionMatera.lecturas sigue tipado como LecturaSensores y el contrato dice Lectura.
# TODO(David): unificar LecturaSensores con Lectura.
@dataclass
class Lectura:                 # en la fase 1 se llamaba LecturaSensores
    dispositivo_id: str
    marca_tiempo: datetime     # UTC, con zona horaria
    humedad: float             # % (0..100)
    luz: float                 # lux (0..150000)
    temperatura: float         # °C (-10..60)
    # TODO(David): __post_init__ con la validación de límites físicos -> ValorFueraDeRangoFisicoError


@dataclass
class EstadoPlanta:
    planta_id: str
    lectura: Lectura
    evaluacion: EvaluacionMatera


@dataclass
class Usuario:
    id: str
    email: str
    password_hash: str


@dataclass
class Planta:
    id: str
    usuario_id: str
    nombre: str
    especie: str

    def verificar_dueno(self, usuario_id: str) -> None:
        # TODO(David): implementación real. Stub mínimo del contrato.
        if self.usuario_id != usuario_id:
            raise AccesoDenegado()


@dataclass
class Dispositivo:
    id: str
    codigo_emparejamiento: str
    planta_id: Optional[str]   # None = sin vincular
    activo: bool
