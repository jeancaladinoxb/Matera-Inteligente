"""Implementa HistorialLecturasPort en SQLite. Solo traduce filas <-> EstadoPlanta."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from adaptadores.salida.bd import conectar
from domain.modelo import (
    EstadoParametro, EstadoPlanta, EvaluacionMatera, IndiceVitalidad, Lectura, LecturaSensores,
)

# Formato fijo: así el orden por texto es el orden cronológico y los duplicados se detectan igual siempre
FORMATO_FECHA = "%Y-%m-%dT%H:%M:%S.%fZ"
LIMITE_MAXIMO = 500


def _a_texto(marca: datetime) -> str:
    if marca.tzinfo is None:
        marca = marca.replace(tzinfo=timezone.utc)
    return marca.astimezone(timezone.utc).strftime(FORMATO_FECHA)


def _a_fecha(texto: str) -> datetime:
    return datetime.strptime(texto, FORMATO_FECHA).replace(tzinfo=timezone.utc)


def _a_estado(fila) -> EstadoPlanta:
    lectura = Lectura(
        dispositivo_id=fila["dispositivo_id"], marca_tiempo=_a_fecha(fila["marca_tiempo"]),
        humedad=fila["humedad"], luz=fila["luz"], temperatura=fila["temperatura"],
    )
    evaluacion = EvaluacionMatera(
        nombre_especie=fila["especie"],
        lecturas=LecturaSensores(fila["humedad"], fila["luz"], fila["temperatura"]),
        estado_humedad=EstadoParametro(fila["estado_humedad"]),
        estado_luz=EstadoParametro(fila["estado_luz"]),
        estado_temperatura=EstadoParametro(fila["estado_temperatura"]),
        indice_vitalidad=IndiceVitalidad(porcentaje=fila["vitalidad"], nivel=fila["nivel"]),
    )
    return EstadoPlanta(planta_id=fila["planta_id"], lectura=lectura, evaluacion=evaluacion)


class HistorialLecturasBd:
    def __init__(self, ruta_db: Union[str, Path]):
        self._ruta_db = ruta_db

    def guardar(self, planta_id: str, lectura: Lectura, evaluacion: EvaluacionMatera) -> bool:
        """True si se guardó; False si ya existía una lectura de ese dispositivo en esa marca de tiempo."""
        try:
            with conectar(self._ruta_db) as conexion:
                conexion.execute(
                    "INSERT INTO lecturas (planta_id, dispositivo_id, marca_tiempo, especie, humedad, luz, "
                    "temperatura, estado_humedad, estado_luz, estado_temperatura, vitalidad, nivel) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        planta_id, lectura.dispositivo_id, _a_texto(lectura.marca_tiempo),
                        evaluacion.nombre_especie, lectura.humedad, lectura.luz, lectura.temperatura,
                        evaluacion.estado_humedad.value, evaluacion.estado_luz.value,
                        evaluacion.estado_temperatura.value,
                        evaluacion.indice_vitalidad.porcentaje, evaluacion.indice_vitalidad.nivel,
                    ),
                )
        except sqlite3.IntegrityError as error:
            # Solo el duplicado (dispositivo, marca de tiempo) es un resultado normal; lo demás se propaga
            if "lecturas.dispositivo_id" in str(error) and "UNIQUE" in str(error):
                return False
            raise
        return True

    def ultima(self, planta_id: str) -> Optional[EstadoPlanta]:
        estados = self.historial(planta_id, 1)
        return estados[0] if estados else None

    def historial(self, planta_id: str, limite: int) -> List[EstadoPlanta]:
        """Del más reciente al más antiguo; el límite se acota entre 1 y LIMITE_MAXIMO."""
        limite = max(1, min(int(limite), LIMITE_MAXIMO))
        with conectar(self._ruta_db) as conexion:
            filas = conexion.execute(
                "SELECT * FROM lecturas WHERE planta_id = ? ORDER BY marca_tiempo DESC, id DESC LIMIT ?",
                (planta_id, limite),
            ).fetchall()
        return [_a_estado(f) for f in filas]
