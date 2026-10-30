import os
import sqlite3
import tempfile
import unittest

from adaptadores.salida.bd import conectar, inicializar_bd

TABLAS = {"usuarios", "plantas", "dispositivos", "lecturas", "especies"}


class TestBd(unittest.TestCase):
    def setUp(self):
        directorio = tempfile.TemporaryDirectory()
        self.addCleanup(directorio.cleanup)   # se borra al terminar, con las conexiones ya cerradas
        self.ruta_db = os.path.join(directorio.name, "prueba.db")

    def _tablas(self):
        with conectar(self.ruta_db) as c:
            filas = c.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        return {f["name"] for f in filas}

    def test_crea_las_cinco_tablas(self):
        inicializar_bd(self.ruta_db)
        self.assertTrue(TABLAS <= self._tablas())

    def test_inicializar_dos_veces(self):
        inicializar_bd(self.ruta_db)
        with conectar(self.ruta_db) as c:
            c.execute("INSERT INTO usuarios VALUES ('u1', 'a@b.co', 'h')")
        inicializar_bd(self.ruta_db)   # idempotente: no borra datos ni falla
        with conectar(self.ruta_db) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0], 1)

    def test_claves_foraneas_se_aplican(self):
        inicializar_bd(self.ruta_db)
        for _ in range(2):   # en cada conexión nueva, no solo en la primera
            with self.assertRaises(sqlite3.IntegrityError):
                with conectar(self.ruta_db) as c:
                    c.execute("INSERT INTO plantas VALUES ('p1', 'no-existe', 'Mi planta', 'Cactus')")

    def test_la_conexion_se_cierra_al_salir(self):
        inicializar_bd(self.ruta_db)
        with conectar(self.ruta_db) as c:
            c.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):
            c.execute("SELECT 1")

    def test_la_conexion_se_cierra_si_hay_error(self):
        inicializar_bd(self.ruta_db)
        with self.assertRaises(ValueError):
            with conectar(self.ruta_db) as c:
                raise ValueError("fallo")
        with self.assertRaises(sqlite3.ProgrammingError):
            c.execute("SELECT 1")

    def test_confirma_al_salir_y_revierte_si_hay_error(self):
        inicializar_bd(self.ruta_db)
        with conectar(self.ruta_db) as c:
            c.execute("INSERT INTO usuarios VALUES ('u1', 'a@b.co', 'h')")
        with self.assertRaises(ValueError):
            with conectar(self.ruta_db) as c:
                c.execute("INSERT INTO usuarios VALUES ('u2', 'c@d.co', 'h')")
                raise ValueError("fallo")
        with conectar(self.ruta_db) as c:
            ids = [f["id"] for f in c.execute("SELECT id FROM usuarios")]
        self.assertEqual(ids, ["u1"])

    def test_el_esquema_se_lee_desde_el_modulo_no_desde_la_carpeta_de_trabajo(self):
        otra_carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(otra_carpeta.cleanup)
        original = os.getcwd()
        os.chdir(otra_carpeta.name)
        self.addCleanup(os.chdir, original)
        inicializar_bd(self.ruta_db)
        self.assertTrue(TABLAS <= self._tablas())


if __name__ == "__main__":
    unittest.main()
