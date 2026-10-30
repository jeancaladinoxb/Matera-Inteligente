"""Implementa TablaReferenciaPort leyendo la tabla `especies` de SQLite."""
from pathlib import Path
from typing import Iterable, List, Optional, Union

from adaptadores.salida.bd import conectar
from domain.modelo import RangoEspecie

_COLUMNAS = "nombre, humedad_min, humedad_max, luz_min, luz_max, temp_min, temp_max"


def _a_rango(fila) -> RangoEspecie:
    return RangoEspecie(
        nombre_especie=fila["nombre"],
        humedad_min=fila["humedad_min"], humedad_max=fila["humedad_max"],
        luz_min=fila["luz_min"], luz_max=fila["luz_max"],
        temp_min=fila["temp_min"], temp_max=fila["temp_max"],
    )


class TablaReferenciaBd:
    """Mismo comportamiento observable que TablaReferenciaCsv: se elige por configuración."""

    def __init__(self, ruta_db: Union[str, Path]):
        self._ruta_db = ruta_db

    def por_especie(self, nombre: str) -> Optional[RangoEspecie]:
        if not nombre:
            return None
        # lower() de SQLite solo conoce ASCII: suficiente para los nombres del catálogo
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT %s FROM especies WHERE lower(nombre) = ?" % _COLUMNAS,
                (nombre.strip().lower(),),
            ).fetchone()
        return _a_rango(fila) if fila else None

    def todas(self) -> List[RangoEspecie]:
        with conectar(self._ruta_db) as conexion:
            filas = conexion.execute("SELECT %s FROM especies ORDER BY rowid" % _COLUMNAS).fetchall()
        return [_a_rango(f) for f in filas]


def cargar_especies(ruta_db: Union[str, Path], rangos: Iterable[RangoEspecie], fuente: Optional[str] = None) -> int:
    """Inserta o reemplaza las especies en la tabla (idempotente). Devuelve cuántas cargó."""
    filas = [
        (r.nombre_especie, r.humedad_min, r.humedad_max, r.luz_min, r.luz_max, r.temp_min, r.temp_max, fuente)
        for r in rangos
    ]
    with conectar(ruta_db) as conexion:
        conexion.executemany(
            "INSERT OR REPLACE INTO especies (%s, fuente) VALUES (?, ?, ?, ?, ?, ?, ?, ?)" % _COLUMNAS,
            filas,
        )
    return len(filas)
