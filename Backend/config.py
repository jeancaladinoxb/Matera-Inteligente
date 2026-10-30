"""Configuración del backend. Es infraestructura: el dominio no la importa."""
import os
from dataclasses import dataclass
from typing import List, Mapping

try:  # python-dotenv es opcional: sin él solo se usa os.environ
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Constantes JWT compartidas con adaptadores/entrada/seguridad.py (deben coincidir con las suyas)
JWT_ALG = "HS256"
JWT_ISS = "matera"
JWT_EXP_USUARIO_MIN = 60
JWT_EXP_DISPOSITIVO_DIAS = 365
SCOPE_USUARIO = "usuario"
SCOPE_DISPOSITIVO = "lecturas:escribir"
TIPO_USUARIO = "usuario"
TIPO_DISPOSITIVO = "dispositivo"

TABLAS_VALIDAS = ("csv", "bd")
LARGO_MINIMO_SECRETO = 16

RUTA_CSV_POR_DEFECTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "infrastructure", "especies.csv")


class ErrorConfiguracion(Exception):
    """La configuración del entorno es inválida o está incompleta."""


@dataclass(frozen=True)
class Config:
    tabla: str                 # "csv" o "bd": qué adaptador de TablaReferenciaPort se usa
    ruta_csv: str
    ruta_db: str
    jwt_secret: str
    cors_origins: List[str]


def cargar_config(env: Mapping[str, str] = os.environ) -> Config:
    """Lee la configuración de las variables de entorno.

    Solo con el os.environ real se carga el .env: así seguridad.py, que lee el secreto
    directo del entorno en cada petición, lo encuentra. Con un diccionario no hay efectos
    secundarios.
    """
    if env is os.environ and load_dotenv is not None:
        load_dotenv()

    tabla = env.get("MATERA_TABLA", "csv").strip().lower()
    if tabla not in TABLAS_VALIDAS:
        raise ErrorConfiguracion(
            "MATERA_TABLA debe ser uno de %s (se recibió %r)" % (", ".join(TABLAS_VALIDAS), tabla)
        )

    # Sin valor por defecto: nunca se arranca con un secreto conocido. El valor no se incluye en el mensaje.
    secreto = env.get("MATERA_JWT_SECRET", "")
    if len(secreto) < LARGO_MINIMO_SECRETO:
        raise ErrorConfiguracion(
            "MATERA_JWT_SECRET falta o mide menos de %d caracteres" % LARGO_MINIMO_SECRETO
        )

    origenes = [o.strip() for o in env.get("MATERA_CORS_ORIGINS", "").split(",") if o.strip()]
    return Config(
        tabla=tabla,
        ruta_csv=env.get("MATERA_CSV") or RUTA_CSV_POR_DEFECTO,
        ruta_db=env.get("MATERA_DB") or "matera.db",
        jwt_secret=secreto,
        cors_origins=origenes,
    )
