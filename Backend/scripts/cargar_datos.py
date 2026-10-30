"""Prepara la base de datos: crea el esquema, carga las especies del CSV y crea dispositivos con su código.

Uso (desde Backend/):  python scripts/cargar_datos.py [--db RUTA] [--csv RUTA] [--dispositivos N]
Imprime la tabla `dispositivo_id | codigo`: el código es lo que el usuario escribe al vincular su planta.
"""
import argparse
import os
import secrets
import sys
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

# Permite ejecutarlo como script (python scripts/cargar_datos.py) además de como módulo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from adaptadores.salida.bd import conectar, inicializar_bd  # noqa: E402
from adaptadores.salida.dispositivo_bd import DispositivoRepositorioBd  # noqa: E402
from adaptadores.salida.tabla_bd import cargar_especies  # noqa: E402
from adaptadores.salida.tabla_csv import TablaReferenciaCsv  # noqa: E402
from config import RUTA_CSV_POR_DEFECTO  # noqa: E402
from domain.modelo import Dispositivo  # noqa: E402

# Mayúsculas y dígitos sin caracteres ambiguos (0/O, 1/I): el código se escribe a mano
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LARGO_CODIGO = 8
FUENTE_ESPECIES = "infrastructure/FUENTES.md"


def generar_codigo() -> str:
    return "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(LARGO_CODIGO))


def _sin_dueno(ruta_db: str) -> List[Tuple[str, str]]:
    with conectar(ruta_db) as conexion:
        filas = conexion.execute(
            "SELECT id, codigo_emparejamiento FROM dispositivos WHERE planta_id IS NULL ORDER BY rowid"
        ).fetchall()
    return [(f["id"], f["codigo_emparejamiento"]) for f in filas]


def crear_dispositivos(ruta_db: str, cantidad: int) -> int:
    """Crea los dispositivos que falten para que haya `cantidad` sin dueño. Devuelve cuántos creó."""
    repositorio = DispositivoRepositorioBd(ruta_db)
    faltan = max(0, cantidad - len(_sin_dueno(ruta_db)))
    for _ in range(faltan):
        codigo = generar_codigo()
        while repositorio.por_codigo(codigo) is not None:   # el código debe ser único
            codigo = generar_codigo()
        repositorio.guardar(Dispositivo(id=uuid.uuid4().hex, codigo_emparejamiento=codigo, planta_id=None, activo=True))
    return faltan


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Carga especies y dispositivos en la base de datos")
    parser.add_argument("--db", default=os.environ.get("MATERA_DB") or "matera.db", help="archivo SQLite (defecto: MATERA_DB o matera.db)")
    parser.add_argument("--csv", default=RUTA_CSV_POR_DEFECTO, help="CSV de especies")
    parser.add_argument("--dispositivos", type=int, default=3, help="dispositivos sin dueño que deben existir (defecto: 3)")
    args = parser.parse_args(argv)
    if args.dispositivos < 0:
        parser.error("--dispositivos no puede ser negativo")

    inicializar_bd(args.db)
    especies = cargar_especies(args.db, TablaReferenciaCsv(args.csv).todas(), fuente=FUENTE_ESPECIES)
    creados = crear_dispositivos(args.db, args.dispositivos)

    print("Base de datos: %s" % args.db)
    print("Especies cargadas: %d | dispositivos nuevos: %d" % (especies, creados))
    print()
    print("%-34s | %s" % ("dispositivo_id", "codigo"))
    print("-" * 34 + "-+-" + "-" * LARGO_CODIGO)
    for dispositivo_id, codigo in _sin_dueno(args.db):
        print("%-34s | %s" % (dispositivo_id, codigo))
    return 0


if __name__ == "__main__":
    sys.exit(main())
