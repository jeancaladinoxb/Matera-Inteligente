"""Ayudas compartidas por las pruebas de los adaptadores de salida."""
import os
import tempfile
import unittest

from adaptadores.salida.bd import inicializar_bd

RUTA_CSV = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "infrastructure", "especies.csv"
)


def crear_bd_temporal(caso: unittest.TestCase) -> str:
    """Crea una BD con el esquema en un archivo temporal que se borra al terminar la prueba (nunca matera.db)."""
    directorio = tempfile.TemporaryDirectory()
    caso.addCleanup(directorio.cleanup)
    ruta_db = os.path.join(directorio.name, "prueba.db")
    inicializar_bd(ruta_db)
    return ruta_db
