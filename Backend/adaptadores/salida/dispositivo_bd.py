"""Implementa DispositivoRepositorioPort en SQLite. Solo traduce filas <-> Dispositivo."""
from pathlib import Path
from typing import Optional, Union

from adaptadores.salida.bd import conectar
from domain.modelo import Dispositivo

_COLUMNAS = "id, codigo_emparejamiento, planta_id, activo"


def _a_dispositivo(fila) -> Dispositivo:
    return Dispositivo(
        id=fila["id"],
        codigo_emparejamiento=fila["codigo_emparejamiento"],
        planta_id=fila["planta_id"],
        activo=bool(fila["activo"]),     # en la BD es 0/1
    )


class DispositivoRepositorioBd:
    def __init__(self, ruta_db: Union[str, Path]):
        self._ruta_db = ruta_db

    def guardar(self, dispositivo: Dispositivo) -> None:
        # Upsert por id: lo usa la vinculación para asignar planta_id a un dispositivo existente
        with conectar(self._ruta_db) as conexion:
            conexion.execute(
                "INSERT INTO dispositivos (id, codigo_emparejamiento, planta_id, activo) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET codigo_emparejamiento = excluded.codigo_emparejamiento, "
                "planta_id = excluded.planta_id, activo = excluded.activo",
                (dispositivo.id, dispositivo.codigo_emparejamiento, dispositivo.planta_id, int(dispositivo.activo)),
            )

    def por_id(self, dispositivo_id: str) -> Optional[Dispositivo]:
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT %s FROM dispositivos WHERE id = ?" % _COLUMNAS, (dispositivo_id,)
            ).fetchone()
        return _a_dispositivo(fila) if fila else None

    def por_codigo(self, codigo: str) -> Optional[Dispositivo]:
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT %s FROM dispositivos WHERE codigo_emparejamiento = ?" % _COLUMNAS, (codigo,)
            ).fetchone()
        return _a_dispositivo(fila) if fila else None
