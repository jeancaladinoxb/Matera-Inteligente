"""Implementa PlantaRepositorioPort en SQLite. Solo traduce filas <-> Planta."""
from pathlib import Path
from typing import List, Optional, Union

from adaptadores.salida.bd import conectar
from domain.modelo import Planta

_COLUMNAS = "id, usuario_id, nombre, especie"


def _a_planta(fila) -> Planta:
    return Planta(id=fila["id"], usuario_id=fila["usuario_id"], nombre=fila["nombre"], especie=fila["especie"])


class PlantaRepositorioBd:
    def __init__(self, ruta_db: Union[str, Path]):
        self._ruta_db = ruta_db

    def guardar(self, planta: Planta) -> None:
        # Upsert por id (no INSERT OR REPLACE: reemplazar borraría la fila y rompería las claves foráneas)
        with conectar(self._ruta_db) as conexion:
            conexion.execute(
                "INSERT INTO plantas (id, usuario_id, nombre, especie) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET usuario_id = excluded.usuario_id, "
                "nombre = excluded.nombre, especie = excluded.especie",
                (planta.id, planta.usuario_id, planta.nombre, planta.especie),
            )

    def por_id(self, planta_id: str) -> Optional[Planta]:
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute("SELECT %s FROM plantas WHERE id = ?" % _COLUMNAS, (planta_id,)).fetchone()
        return _a_planta(fila) if fila else None

    def de_usuario(self, usuario_id: str) -> List[Planta]:
        with conectar(self._ruta_db) as conexion:
            filas = conexion.execute(
                "SELECT %s FROM plantas WHERE usuario_id = ? ORDER BY rowid" % _COLUMNAS, (usuario_id,)
            ).fetchall()
        return [_a_planta(f) for f in filas]
