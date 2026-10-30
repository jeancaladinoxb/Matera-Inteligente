import unittest

from adaptadores.salida.bd import conectar
from adaptadores.salida.tabla_bd import TablaReferenciaBd, cargar_especies
from adaptadores.salida.tabla_csv import TablaReferenciaCsv
from tests.salida.contrato_tabla import ContratoTablaReferencia
from tests.salida.utiles import RUTA_CSV, crear_bd_temporal


class TestTablaBd(ContratoTablaReferencia, unittest.TestCase):
    def crear_tabla(self):
        self.ruta_db = crear_bd_temporal(self)
        cargar_especies(self.ruta_db, TablaReferenciaCsv(RUTA_CSV).todas())
        return TablaReferenciaBd(self.ruta_db)

    def test_da_los_mismos_resultados_que_la_tabla_csv(self):
        csv = TablaReferenciaCsv(RUTA_CSV)
        self.assertEqual(self.tabla.todas(), csv.todas())
        for nombre in ("Orquidea", " cactus ", "FICUS", "Baobab", ""):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.tabla.por_especie(nombre), csv.por_especie(nombre))

    def test_cargar_especies_es_idempotente(self):
        cargar_especies(self.ruta_db, TablaReferenciaCsv(RUTA_CSV).todas(), fuente="FUENTES.md")
        cargar_especies(self.ruta_db, TablaReferenciaCsv(RUTA_CSV).todas(), fuente="FUENTES.md")
        self.assertEqual(len(self.tabla.todas()), 5)
        with conectar(self.ruta_db) as c:
            self.assertEqual(c.execute("SELECT fuente FROM especies LIMIT 1").fetchone()[0], "FUENTES.md")

    def test_tabla_vacia(self):
        vacia = TablaReferenciaBd(crear_bd_temporal(self))
        self.assertEqual(vacia.todas(), [])
        self.assertIsNone(vacia.por_especie("Cactus"))


if __name__ == "__main__":
    unittest.main()
