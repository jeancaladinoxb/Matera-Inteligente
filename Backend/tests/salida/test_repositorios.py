import sqlite3
import unittest

from adaptadores.salida.dispositivo_bd import DispositivoRepositorioBd
from adaptadores.salida.planta_bd import PlantaRepositorioBd
from adaptadores.salida.usuario_bd import UsuarioRepositorioBd
from domain.excepciones_cuentas import UsuarioYaExiste
from domain.modelo import Dispositivo, Planta, Usuario
from tests.salida.utiles import crear_bd_temporal


class TestUsuarioRepositorio(unittest.TestCase):
    def setUp(self):
        self.repo = UsuarioRepositorioBd(crear_bd_temporal(self))

    def test_guardar_y_buscar(self):
        self.repo.guardar(Usuario("u1", "ana@correo.co", "hash1"))
        self.assertEqual(self.repo.por_id("u1"), Usuario("u1", "ana@correo.co", "hash1"))
        self.assertEqual(self.repo.por_email("ana@correo.co").id, "u1")

    def test_inexistente(self):
        self.assertIsNone(self.repo.por_id("nada"))
        self.assertIsNone(self.repo.por_email("nadie@correo.co"))

    def test_email_se_guarda_normalizado_y_se_busca_normalizado(self):
        self.repo.guardar(Usuario("u1", "  Ana@Correo.CO ", "h"))
        self.assertEqual(self.repo.por_id("u1").email, "ana@correo.co")
        self.assertEqual(self.repo.por_email(" ANA@correo.co").id, "u1")

    def test_email_repetido(self):
        self.repo.guardar(Usuario("u1", "ana@correo.co", "h"))
        with self.assertRaises(UsuarioYaExiste):
            self.repo.guardar(Usuario("u2", "ANA@correo.co ", "h"))
        self.assertIsNone(self.repo.por_id("u2"))

    def test_otro_error_de_integridad_no_se_confunde_con_email_repetido(self):
        self.repo.guardar(Usuario("u1", "ana@correo.co", "h"))
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            self.repo.guardar(Usuario("u1", "otra@correo.co", "h"))   # mismo id, otro correo
        self.assertNotIsInstance(ctx.exception, UsuarioYaExiste)


class TestPlantaRepositorio(unittest.TestCase):
    def setUp(self):
        ruta = crear_bd_temporal(self)
        usuarios = UsuarioRepositorioBd(ruta)
        usuarios.guardar(Usuario("u1", "a@correo.co", "h"))
        usuarios.guardar(Usuario("u2", "b@correo.co", "h"))
        self.repo = PlantaRepositorioBd(ruta)

    def test_guardar_y_buscar(self):
        self.repo.guardar(Planta("p1", "u1", "Mi cactus", "Cactus"))
        self.assertEqual(self.repo.por_id("p1"), Planta("p1", "u1", "Mi cactus", "Cactus"))
        self.assertIsNone(self.repo.por_id("nada"))

    def test_de_usuario_solo_trae_las_suyas(self):
        self.repo.guardar(Planta("p1", "u1", "A", "Cactus"))
        self.repo.guardar(Planta("p2", "u2", "B", "Ficus"))
        self.repo.guardar(Planta("p3", "u1", "C", "Helecho"))
        self.assertEqual([p.id for p in self.repo.de_usuario("u1")], ["p1", "p3"])
        self.assertEqual([p.id for p in self.repo.de_usuario("u2")], ["p2"])
        self.assertEqual(self.repo.de_usuario("nadie"), [])

    def test_guardar_dos_veces_actualiza(self):
        self.repo.guardar(Planta("p1", "u1", "A", "Cactus"))
        self.repo.guardar(Planta("p1", "u1", "Nuevo nombre", "Cactus"))
        self.assertEqual(self.repo.por_id("p1").nombre, "Nuevo nombre")
        self.assertEqual(len(self.repo.de_usuario("u1")), 1)


class TestDispositivoRepositorio(unittest.TestCase):
    def setUp(self):
        ruta = crear_bd_temporal(self)
        UsuarioRepositorioBd(ruta).guardar(Usuario("u1", "a@correo.co", "h"))
        PlantaRepositorioBd(ruta).guardar(Planta("p1", "u1", "A", "Cactus"))
        self.repo = DispositivoRepositorioBd(ruta)

    def test_guardar_y_buscar_por_id_y_por_codigo(self):
        self.repo.guardar(Dispositivo("d1", "ABCD2345", None, True))
        self.assertEqual(self.repo.por_id("d1"), Dispositivo("d1", "ABCD2345", None, True))
        self.assertEqual(self.repo.por_codigo("ABCD2345").id, "d1")
        self.assertIsNone(self.repo.por_id("nada"))
        self.assertIsNone(self.repo.por_codigo("ZZZZ9999"))

    def test_activo_es_bool_en_ambos_sentidos(self):
        self.repo.guardar(Dispositivo("d1", "AAAA2222", None, True))
        self.repo.guardar(Dispositivo("d2", "BBBB3333", None, False))
        self.assertIs(self.repo.por_id("d1").activo, True)
        self.assertIs(self.repo.por_id("d2").activo, False)

    def test_upsert_asigna_planta_id_sin_duplicar(self):
        self.repo.guardar(Dispositivo("d1", "ABCD2345", None, True))
        self.repo.guardar(Dispositivo("d1", "ABCD2345", "p1", True))
        self.assertEqual(self.repo.por_id("d1").planta_id, "p1")
        self.assertEqual(self.repo.por_codigo("ABCD2345").planta_id, "p1")

    def test_codigo_repetido_en_otro_dispositivo_falla(self):
        self.repo.guardar(Dispositivo("d1", "ABCD2345", None, True))
        with self.assertRaises(sqlite3.IntegrityError):
            self.repo.guardar(Dispositivo("d2", "ABCD2345", None, True))


if __name__ == "__main__":
    unittest.main()
