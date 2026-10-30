"""Los servicios de cuentas conectados a los adaptadores reales (SQLite, werkzeug, PyJWT), como en create_app()."""
import os
import unittest
from unittest.mock import patch

from flask import Flask, jsonify

from adaptadores.entrada.seguridad import dispositivo_requerido, usuario_requerido
from adaptadores.salida.dispositivo_bd import DispositivoRepositorioBd
from adaptadores.salida.emisor_jwt import EmisorJwt
from adaptadores.salida.hasher_password import HasherPassword
from adaptadores.salida.planta_bd import PlantaRepositorioBd
from adaptadores.salida.tabla_bd import TablaReferenciaBd, cargar_especies
from adaptadores.salida.tabla_csv import TablaReferenciaCsv
from adaptadores.salida.usuario_bd import UsuarioRepositorioBd
from domain.excepciones import DispositivoYaVinculado
from domain.excepciones_cuentas import CredencialesInvalidas, UsuarioYaExiste
from domain.modelo import Dispositivo
from domain.servicios_cuentas import AutenticarUsuarioServicio, VincularDispositivoServicio
from tests.salida.utiles import RUTA_CSV, crear_bd_temporal

SECRETO = "secreto-de-prueba-de-16+"


def _app():
    app = Flask(__name__)

    @app.get("/usuario")
    @usuario_requerido
    def usuario(usuario_id):
        return jsonify({"usuario_id": usuario_id})

    @app.get("/dispositivo")
    @dispositivo_requerido
    def dispositivo(dispositivo_id, planta_id):
        return jsonify({"dispositivo_id": dispositivo_id, "planta_id": planta_id})

    return app


class TestIntegracionCuentas(unittest.TestCase):
    def setUp(self):
        patcher = patch.dict(os.environ, {"MATERA_JWT_SECRET": SECRETO})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ruta_db = crear_bd_temporal(self)
        cargar_especies(self.ruta_db, TablaReferenciaCsv(RUTA_CSV).todas())
        self.usuarios = UsuarioRepositorioBd(self.ruta_db)
        self.plantas = PlantaRepositorioBd(self.ruta_db)
        self.dispositivos = DispositivoRepositorioBd(self.ruta_db)
        self.dispositivos.guardar(Dispositivo("d1", "ABCD2345", None, True))
        emisor = EmisorJwt(SECRETO)
        self.autenticar = AutenticarUsuarioServicio(self.usuarios, HasherPassword(), emisor)
        self.emisor = emisor
        self.cliente = _app().test_client()

    def _vincular_servicio(self, tabla):
        return VincularDispositivoServicio(self.plantas, self.dispositivos, tabla, self.emisor)

    def test_registro_login_y_token_aceptado_por_seguridad(self):
        usuario = self.autenticar.registrar("Ana@Correo.co", "clave-12345")
        token = self.autenticar.iniciar_sesion("ana@correo.co", "clave-12345")
        r = self.cliente.get("/usuario", headers={"Authorization": "Bearer " + token})
        self.assertEqual(r.get_json(), {"usuario_id": usuario.id})
        with self.assertRaises(UsuarioYaExiste):
            self.autenticar.registrar("ANA@correo.co", "otra-clave-123")
        with self.assertRaises(CredencialesInvalidas):
            self.autenticar.iniciar_sesion("ana@correo.co", "equivocada-1")

    def test_vincular_con_cualquiera_de_las_dos_tablas(self):
        usuario = self.autenticar.registrar("ana@correo.co", "clave-12345")
        tablas = {"csv": TablaReferenciaCsv(RUTA_CSV), "bd": TablaReferenciaBd(self.ruta_db)}
        for i, (nombre, tabla) in enumerate(tablas.items()):
            with self.subTest(tabla=nombre):
                self.dispositivos.guardar(Dispositivo("dx%d" % i, "COD%d2345" % i, None, True))
                r = self._vincular_servicio(tabla).vincular(usuario.id, "Mi planta", "cactus", "COD%d2345" % i)
                self.assertEqual(self.plantas.por_id(r.planta_id).especie, "Cactus")
                self.assertEqual(self.dispositivos.por_id("dx%d" % i).planta_id, r.planta_id)
                resp = self.cliente.get("/dispositivo", headers={"Authorization": "Bearer " + r.token_dispositivo})
                self.assertEqual(resp.get_json(), {"dispositivo_id": "dx%d" % i, "planta_id": r.planta_id})
        self.assertEqual(len(self.plantas.de_usuario(usuario.id)), 2)

    def test_segundo_intento_con_el_mismo_codigo_falla(self):
        usuario = self.autenticar.registrar("ana@correo.co", "clave-12345")
        servicio = self._vincular_servicio(TablaReferenciaBd(self.ruta_db))
        servicio.vincular(usuario.id, "Mi planta", "Ficus", "ABCD2345")
        with self.assertRaises(DispositivoYaVinculado):
            servicio.vincular(usuario.id, "Otra", "Ficus", "ABCD2345")


if __name__ == "__main__":
    unittest.main()
