"""Conexión y esquema de SQLite. Es lo único que sabe dónde está el archivo de la base de datos."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

# Relativa a este archivo, no a la carpeta de trabajo
_RUTA_ESQUEMA = Path(__file__).resolve().with_name("esquema.sql")


@contextmanager
def conectar(ruta_db: Union[str, Path]) -> Iterator[sqlite3.Connection]:
    """Abre una conexión por operación: confirma si todo sale bien, revierte si hay error y siempre cierra.

    Flask atiende peticiones en varios hilos, así que no se comparte una conexión global.
    """
    conexion = sqlite3.connect(str(ruta_db))
    conexion.row_factory = sqlite3.Row
    # Las claves foráneas valen por conexión: hay que activarlas en cada una
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except BaseException:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar_bd(ruta_db: Union[str, Path]) -> None:
    """Crea las tablas si no existen (se puede llamar varias veces)."""
    with conectar(ruta_db) as conexion:
        conexion.executescript(_RUTA_ESQUEMA.read_text(encoding="utf-8"))
