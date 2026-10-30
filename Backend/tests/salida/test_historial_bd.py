import sqlite3
import unittest
from datetime import datetime, timedelta, timezone

from adaptadores.salida.historial_bd import LIMITE_MAXIMO, HistorialLecturasBd
from adaptadores.salida.planta_bd import PlantaRepositorioBd
from adaptadores.salida.usuario_bd import UsuarioRepositorioBd
from domain.modelo import (
    EstadoParametro, EvaluacionMatera, IndiceVitalidad, Lectura, Planta, Usuario,
)
from tests.salida.utiles import crear_bd_temporal

INICIO = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)


def _lectura(minutos=0, dispositivo="d1", humedad=55.0):
    return Lectura(dispositivo, INICIO + timedelta(minutes=minutos), humedad, 15000.0, 21.5)


def _evaluacion(lectura, especie="Orquidea"):
    return EvaluacionMatera(
        especie, lectura,
        EstadoParametro.OPTIMO, EstadoParametro.ALTO, EstadoParametro.BAJO, IndiceVitalidad(83.33, "BUENO"),
    )


class TestHistorialBd(unittest.TestCase):
    def setUp(self):
        ruta = crear_bd_temporal(self)
        UsuarioRepositorioBd(ruta).guardar(Usuario("u1", "a@correo.co", "h"))
        plantas = PlantaRepositorioBd(ruta)
        plantas.guardar(Planta("p1", "u1", "A", "Orquidea"))
        plantas.guardar(Planta("p2", "u1", "B", "Cactus"))
        self.historial = HistorialLecturasBd(ruta)

    def _guardar(self, planta="p1", **kwargs):
        lectura = _lectura(**kwargs)
        return self.historial.guardar(planta, lectura, _evaluacion(lectura))

    def test_guardar_devuelve_true_y_duplicado_false(self):
        self.assertTrue(self._guardar(minutos=0))
        self.assertFalse(self._guardar(minutos=0))                      # mismo dispositivo y marca de tiempo
        self.assertTrue(self._guardar(minutos=0, dispositivo="d2"))     # otro dispositivo: no es duplicado
        self.assertTrue(self._guardar(minutos=1))                       # otra marca de tiempo
        self.assertEqual(len(self.historial.historial("p1", 10)), 3)

    def test_planta_inexistente_no_se_confunde_con_duplicado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self._guardar(planta="no-existe")

    def test_ultima_y_sin_lecturas(self):
        self.assertIsNone(self.historial.ultima("p1"))
        self._guardar(minutos=0)
        self._guardar(minutos=5)
        self._guardar(minutos=2)
        self.assertEqual(self.historial.ultima("p1").lectura.marca_tiempo, INICIO + timedelta(minutes=5))

    def test_historial_ordenado_del_mas_reciente_y_con_limite(self):
        for minuto in (3, 1, 4, 0, 2):    # insertadas en desorden
            self._guardar(minutos=minuto)
        todas = self.historial.historial("p1", 10)
        self.assertEqual([e.lectura.marca_tiempo for e in todas], [INICIO + timedelta(minutes=m) for m in (4, 3, 2, 1, 0)])
        self.assertEqual(len(self.historial.historial("p1", 2)), 2)
        self.assertEqual(self.historial.historial("p1", 2)[0].lectura.marca_tiempo, INICIO + timedelta(minutes=4))

    def test_el_limite_se_acota(self):
        self._guardar(minutos=0)
        self.assertEqual(len(self.historial.historial("p1", 0)), 1)       # mínimo 1
        self.assertEqual(len(self.historial.historial("p1", -5)), 1)
        self.assertEqual(len(self.historial.historial("p1", 10 ** 6)), 1)  # máximo LIMITE_MAXIMO
        self.assertEqual(LIMITE_MAXIMO, 500)

    def test_solo_trae_las_lecturas_de_la_planta(self):
        self._guardar(planta="p1", minutos=0)
        self._guardar(planta="p2", minutos=1, dispositivo="d2")
        self.assertEqual([e.planta_id for e in self.historial.historial("p2", 10)], ["p2"])

    def test_reconstruye_el_estado_completo(self):
        lectura = _lectura(minutos=7, humedad=61.5)
        evaluacion = _evaluacion(lectura, especie="Orquidea")
        self.historial.guardar("p1", lectura, evaluacion)
        estado = self.historial.ultima("p1")
        self.assertEqual(estado.planta_id, "p1")
        self.assertEqual(estado.lectura, lectura)                   # incluye zona horaria UTC
        self.assertEqual(estado.lectura.marca_tiempo.tzinfo, timezone.utc)
        self.assertEqual(estado.evaluacion, evaluacion)
        self.assertIs(estado.evaluacion.estado_luz, EstadoParametro.ALTO)
        self.assertEqual(estado.evaluacion.indice_vitalidad, IndiceVitalidad(83.33, "BUENO"))

    def test_marca_de_tiempo_con_otra_zona_se_guarda_en_utc(self):
        zona = timezone(timedelta(hours=-5))
        lectura = Lectura("d1", datetime(2026, 5, 1, 7, 0, 0, tzinfo=zona), 50.0, 1000.0, 20.0)   # = 12:00 UTC
        self.historial.guardar("p1", lectura, _evaluacion(lectura))
        self.assertEqual(self.historial.ultima("p1").lectura.marca_tiempo, INICIO)
        self.assertFalse(self._guardar(minutos=0))     # la misma hora en UTC es un duplicado


if __name__ == "__main__":
    unittest.main()
