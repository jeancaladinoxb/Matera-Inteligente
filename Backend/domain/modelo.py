"""Modelo del dominio de la matera.

Solo biblioteca estandar: ni flask, ni jwt, ni csv, ni sqlite3, ni json.
Las entidades protegen sus invariantes en el constructor, de modo que no puede
existir en memoria una Lectura fisicamente imposible ni un rango invertido.

Reemplaza el contrato provisional del commit 0. Conserva los nombres, los
campos y el orden que fijan tests/dominio/test_contrato_modelo.py y
test_contrato_puertos.py.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from domain.excepciones import AccesoDenegado, ValorFueraDeRangoFisicoError

# Limites fisicos razonables de cada sensor. Nada que ver con los rangos
# ideales de una especie: estos dicen si la medicion es creible.
LIMITES_FISICOS = {
    "humedad": (0.0, 100.0, "%"),
    "luz": (0.0, 150000.0, "lux"),
    "temperatura": (-10.0, 60.0, "°C"),
}

# Niveles del indice de vitalidad. Son texto, no enum, porque se guardan y se
# leen tal cual en la columna "nivel" de la tabla lecturas.
NIVEL_EXCELENTE = "EXCELENTE"
NIVEL_BUENO = "BUENO"
NIVEL_REGULAR = "REGULAR"
NIVEL_CRITICO = "CRITICO"


def nuevo_id() -> str:
    """Identificador de una entidad nueva.

    Lo genera el dominio y no la base de datos, para que los casos de uso se
    puedan probar sin nada que asigne llaves.
    """
    return uuid.uuid4().hex


def ahora() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Lecturas y evaluacion
# --------------------------------------------------------------------------

class EstadoParametro(Enum):
    """Posicion de un parametro medido respecto al rango ideal de la especie."""

    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"


@dataclass(frozen=True)
class IndiceVitalidad:
    porcentaje: float            # 0.0 a 100.0
    nivel: str                   # EXCELENTE, BUENO, REGULAR, CRITICO

    def __post_init__(self):
        if not (0.0 <= self.porcentaje <= 100.0):
            raise ValueError("El porcentaje de vitalidad debe estar entre 0.0 y 100.0")


@dataclass
class Lectura:
    """Una medicion tomada por un dispositivo en un instante.

    Unifica la LecturaSensores de la fase 1: ahora una lectura sabe de donde
    vino y cuando se tomo, que es lo que necesita el historial.
    """

    dispositivo_id: str
    marca_tiempo: datetime       # UTC, con zona horaria
    humedad: float               # % (0..100)
    luz: float                   # lux (0..150000)
    temperatura: float           # C (-10..60)

    def __post_init__(self):
        for campo in ("humedad", "luz", "temperatura"):
            valor = getattr(self, campo)
            minimo, maximo, unidad = LIMITES_FISICOS[campo]
            # bool es subclase de int: True pasaria como 1.0 si no se excluye
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValorFueraDeRangoFisicoError(campo, valor, minimo, maximo, unidad)
            if not (minimo <= float(valor) <= maximo):
                raise ValorFueraDeRangoFisicoError(campo, valor, minimo, maximo, unidad)


# La fase 1 la llamaba asi. Se conserva el nombre para no romper imports
# viejos, pero es la misma clase: ya no hay dos formas de una lectura.
LecturaSensores = Lectura


@dataclass
class RangoEspecie:
    """Rangos ideales de una especie. Es la tabla de referencia del enunciado."""

    nombre_especie: str
    humedad_min: float
    humedad_max: float
    luz_min: float
    luz_max: float
    temp_min: float
    temp_max: float

    @property
    def nombre(self) -> str:
        """Alias que usan los adaptadores de entrada."""
        return self.nombre_especie

    def __post_init__(self):
        for etiqueta, minimo, maximo in (
            ("humedad", self.humedad_min, self.humedad_max),
            ("luz", self.luz_min, self.luz_max),
            ("temperatura", self.temp_min, self.temp_max),
        ):
            if minimo > maximo:
                raise ValueError(
                    "El rango de %s de '%s' esta invertido: %s > %s"
                    % (etiqueta, self.nombre_especie, minimo, maximo)
                )


@dataclass
class EvaluacionMatera:
    """Resultado de comparar una lectura con el rango de su especie."""

    nombre_especie: str
    lecturas: Lectura
    estado_humedad: EstadoParametro
    estado_luz: EstadoParametro
    estado_temperatura: EstadoParametro
    indice_vitalidad: IndiceVitalidad

    def todos_en_rango(self) -> bool:
        return all(
            estado is EstadoParametro.OPTIMO
            for estado in (self.estado_humedad, self.estado_luz, self.estado_temperatura)
        )


@dataclass
class EstadoPlanta:
    """Lo que ve el usuario: una lectura de su planta, ya evaluada."""

    planta_id: str
    lectura: Lectura
    evaluacion: EvaluacionMatera


# --------------------------------------------------------------------------
# Usuarios, plantas y dispositivos
# --------------------------------------------------------------------------

@dataclass
class Usuario:
    id: str
    email: str
    password_hash: str


@dataclass
class Planta:
    """Cada planta pertenece a exactamente un usuario (requisito R7)."""

    id: str
    usuario_id: str
    nombre: str
    especie: str

    @property
    def planta_id(self) -> str:
        """Alias que usan los adaptadores de entrada."""
        return self.id

    def verificar_dueno(self, usuario_id: str) -> None:
        """Regla de negocio: solo el dueno consulta su planta.

        Vive en el dominio a proposito. El adaptador verifica el token y dice
        QUIEN es; quien decide si ese alguien puede ver esta planta es la
        entidad.
        """
        if self.usuario_id != usuario_id:
            raise AccesoDenegado("La planta no pertenece al usuario")


@dataclass
class Dispositivo:
    """Un ESP32. Nace en fabrica con un codigo de emparejamiento y sin dueno."""

    id: str
    codigo_emparejamiento: str
    planta_id: Optional[str]     # None = sin vincular
    activo: bool

    def esta_vinculado(self) -> bool:
        return self.planta_id is not None

    def verificar_activo(self) -> None:
        from domain.excepciones import DispositivoInactivo

        if not self.activo:
            raise DispositivoInactivo("El dispositivo esta inactivo")


def especies_ordenadas(rangos: List[RangoEspecie]) -> List[RangoEspecie]:
    return sorted(rangos, key=lambda rango: rango.nombre_especie.lower())
