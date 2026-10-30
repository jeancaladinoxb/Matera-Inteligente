# PROVISIONAL (Julián, commit 0): prueba de humo del contrato provisional de domain/modelo.py.
import unittest
from datetime import datetime, timezone

from domain.excepciones import AccesoDenegado
from domain.modelo import (
    Dispositivo, EstadoParametro, EstadoPlanta, EvaluacionMatera, IndiceVitalidad,
    Lectura, Planta, RangoEspecie, Usuario,
)


class TestModeloHumo(unittest.TestCase):
    def test_se_instancian_todas_las_clases(self):
        marca = datetime(2026, 1, 1, tzinfo=timezone.utc)
        lectura = Lectura("d1", marca, 50.0, 10000.0, 20.0)
        evaluacion = EvaluacionMatera(
            "Orquidea", Lectura("d-1", datetime.now(timezone.utc), 50.0, 10000.0, 20.0),
            EstadoParametro.OPTIMO, EstadoParametro.OPTIMO, EstadoParametro.OPTIMO,
            IndiceVitalidad(100.0, "EXCELENTE"),
        )
        estado = EstadoPlanta("p1", lectura, evaluacion)
        self.assertEqual(estado.lectura.dispositivo_id, "d1")
        RangoEspecie("Orquidea", 40, 70, 10000, 20000, 18, 25)
        Usuario("u1", "a@b.co", "hash")
        Dispositivo("d1", "ABCD2345", None, True)

    def test_verificar_dueno(self):
        planta = Planta("p1", "u1", "Mi planta", "Orquidea")
        planta.verificar_dueno("u1")
        with self.assertRaises(AccesoDenegado):
            planta.verificar_dueno("otro")


if __name__ == "__main__":
    unittest.main()
