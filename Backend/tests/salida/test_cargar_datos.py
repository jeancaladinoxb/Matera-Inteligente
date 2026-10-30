import contextlib
import io
import os
import re
import tempfile
import unittest

from adaptadores.salida.bd import conectar
from adaptadores.salida.tabla_bd import TablaReferenciaBd
from scripts import cargar_datos
from tests.salida.utiles import RUTA_CSV


class TestCargarDatos(unittest.TestCase):
    def setUp(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        self.ruta_db = os.path.join(directorio.name, "prueba.db")   # nunca matera.db

    def _ejecutar(self, *extra):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = cargar_datos.main(["--db", self.ruta_db, "--csv", RUTA_CSV] + list(extra))
        self.assertEqual(codigo, 0)
        return salida.getvalue()

    def _dispositivos(self):
        with conectar(self.ruta_db) as c:
            return [(f["id"], f["codigo_emparejamiento"]) for f in c.execute("SELECT * FROM dispositivos")]

    def test_deja_la_bd_lista(self):
        texto = self._ejecutar()
        self.assertEqual(len(TablaReferenciaBd(self.ruta_db).todas()), 5)
        dispositivos = self._dispositivos()
        self.assertEqual(len(dispositivos), 3)
        for dispositivo_id, codigo in dispositivos:      # la tabla impresa trae cada id y cada código
            self.assertIn(dispositivo_id, texto)
            self.assertIn(codigo, texto)

    def test_es_idempotente(self):
        self._ejecutar("--dispositivos", "3")
        antes = self._dispositivos()
        self._ejecutar("--dispositivos", "3")
        self.assertEqual(self._dispositivos(), antes)
        self.assertEqual(len(TablaReferenciaBd(self.ruta_db).todas()), 5)

    def test_cantidad_configurable_y_solo_crea_los_que_faltan(self):
        self._ejecutar("--dispositivos", "2")
        self._ejecutar("--dispositivos", "5")
        self.assertEqual(len(self._dispositivos()), 5)

    def test_los_codigos_son_legibles_y_unicos(self):
        self._ejecutar("--dispositivos", "50")
        codigos = [c for _, c in self._dispositivos()]
        self.assertEqual(len(set(codigos)), 50)
        for codigo in codigos:
            self.assertRegex(codigo, r"^[A-Z2-9]{8}$")
            self.assertIsNone(re.search(r"[01OI]", codigo))

    def test_generar_codigo_no_usa_caracteres_ambiguos(self):
        for _ in range(200):
            self.assertIsNone(re.search(r"[01OI]", cargar_datos.generar_codigo()))

    def test_cantidad_negativa_es_un_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            cargar_datos.main(["--db", self.ruta_db, "--dispositivos", "-1"])


if __name__ == "__main__":
    unittest.main()
