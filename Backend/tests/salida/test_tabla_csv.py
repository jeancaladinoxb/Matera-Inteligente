import os
import tempfile
import unittest

from adaptadores.salida.tabla_csv import TablaReferenciaCsv
from tests.salida.contrato_tabla import ContratoTablaReferencia
from tests.salida.utiles import RUTA_CSV


class TestTablaCsv(ContratoTablaReferencia, unittest.TestCase):
    def crear_tabla(self):
        return TablaReferenciaCsv(RUTA_CSV)

    def test_carga_el_archivo_una_sola_vez(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        ruta = os.path.join(directorio.name, "e.csv")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("especie,humedad_min,humedad_max,luz_min,luz_max,temp_min,temp_max\nCactus,10,30,25000,50000,15,35\n")
        tabla = TablaReferenciaCsv(ruta)
        os.remove(ruta)   # si volviera a leer el archivo, fallaría
        self.assertEqual(tabla.por_especie("cactus").nombre_especie, "Cactus")
        self.assertEqual(len(tabla.todas()), 1)

    def test_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            TablaReferenciaCsv("no/existe.csv")


if __name__ == "__main__":
    unittest.main()
