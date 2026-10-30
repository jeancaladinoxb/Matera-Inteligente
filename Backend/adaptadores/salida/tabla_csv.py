"""Implementa TablaReferenciaPort leyendo el CSV de especies."""
import csv
from typing import Dict, List, Optional

from domain.modelo import RangoEspecie


class TablaReferenciaCsv:
    """Tabla de referencia de especies en un archivo CSV (se lee una sola vez, al crearla)."""

    def __init__(self, ruta_csv: str):
        self._por_nombre: Dict[str, RangoEspecie] = {}
        with open(ruta_csv, mode="r", encoding="utf-8", newline="") as archivo:
            for fila in csv.DictReader(archivo):
                nombre = fila["especie"].strip()
                self._por_nombre[nombre.lower()] = RangoEspecie(
                    nombre_especie=nombre,
                    humedad_min=float(fila["humedad_min"]),
                    humedad_max=float(fila["humedad_max"]),
                    luz_min=float(fila["luz_min"]),
                    luz_max=float(fila["luz_max"]),
                    temp_min=float(fila["temp_min"]),
                    temp_max=float(fila["temp_max"]),
                )

    def por_especie(self, nombre: str) -> Optional[RangoEspecie]:
        if not nombre:
            return None
        return self._por_nombre.get(nombre.strip().lower())

    def todas(self) -> List[RangoEspecie]:
        return list(self._por_nombre.values())
