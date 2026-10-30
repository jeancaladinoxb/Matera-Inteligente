# PROVISIONAL (Julián, commit 0): prueba de contrato del dominio. Si David reemplaza modelo.py y cambia
# un nombre o campo acordado, esta prueba falla indicando cuál.
import dataclasses
import unittest

from domain.modelo import (
    Dispositivo, EstadoParametro, EstadoPlanta, EvaluacionMatera, IndiceVitalidad,
    Lectura, Planta, RangoEspecie, Usuario,
)

CAMPOS_ACORDADOS = {
    Lectura: ["dispositivo_id", "marca_tiempo", "humedad", "luz", "temperatura"],
    RangoEspecie: [
        "nombre_especie", "humedad_min", "humedad_max", "luz_min", "luz_max", "temp_min", "temp_max",
    ],
    EvaluacionMatera: [
        "nombre_especie", "lecturas", "estado_humedad", "estado_luz", "estado_temperatura",
        "indice_vitalidad",
    ],
    EstadoPlanta: ["planta_id", "lectura", "evaluacion"],
    Usuario: ["id", "email", "password_hash"],
    Planta: ["id", "usuario_id", "nombre", "especie"],
    Dispositivo: ["id", "codigo_emparejamiento", "planta_id", "activo"],
    IndiceVitalidad: ["porcentaje", "nivel"],
}


class TestContratoModelo(unittest.TestCase):
    def test_campos_exactos_de_cada_entidad(self):
        for clase, esperados in CAMPOS_ACORDADOS.items():
            with self.subTest(entidad=clase.__name__):
                reales = [f.name for f in dataclasses.fields(clase)]
                faltan = [c for c in esperados if c not in reales]
                sobran = [c for c in reales if c not in esperados]
                self.assertEqual(
                    reales, esperados,
                    "%s rompe el contrato. Faltan: %s. Sobran: %s. (el orden también cuenta)"
                    % (clase.__name__, faltan or "ninguno", sobran or "ninguno"),
                )

    def test_estado_parametro(self):
        self.assertEqual({e.name for e in EstadoParametro}, {"BAJO", "OPTIMO", "ALTO"})

    def test_planta_tiene_verificar_dueno(self):
        self.assertTrue(
            callable(getattr(Planta, "verificar_dueno", None)),
            "Planta.verificar_dueno no existe: es parte del contrato",
        )


if __name__ == "__main__":
    unittest.main()
