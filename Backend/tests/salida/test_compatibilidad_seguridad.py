"""Un token emitido por EmisorJwt debe ser aceptado por adaptadores/entrada/seguridad.py (y los incorrectos, rechazados).
Usa una mini app Flask propia: no toca app.py."""
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from flask import Flask, jsonify

from adaptadores.entrada.seguridad import dispositivo_requerido, usuario_requerido
from adaptadores.salida.emisor_jwt import EmisorJwt

SECRETO = "secreto-de-prueba-de-16+"


def _crear_app():
    app = Flask(__name__)

    @app.get("/usuario")
    @usuario_requerido
    def ruta_usuario(usuario_id):
        return jsonify({"usuario_id": usuario_id})

    @app.get("/dispositivo")
    @dispositivo_requerido
    def ruta_dispositivo(dispositivo_id, planta_id):
        return jsonify({"dispositivo_id": dispositivo_id, "planta_id": planta_id})

    return app


def _cabecera(token):
    return {"Authorization": "Bearer " + token}


class TestCompatibilidadConSeguridad(unittest.TestCase):
    def setUp(self):
        # El secreto vale solo durante la prueba; patch.dict restaura el entorno al terminar
        patcher = patch.dict(os.environ, {"MATERA_JWT_SECRET": SECRETO})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cliente = _crear_app().test_client()
        self.emisor = EmisorJwt(SECRETO)

    def test_token_de_usuario_aceptado_en_ruta_de_usuario(self):
        r = self.cliente.get("/usuario", headers=_cabecera(self.emisor.token_usuario("u1")))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"usuario_id": "u1"})

    def test_token_de_usuario_rechazado_en_ruta_de_dispositivo(self):
        r = self.cliente.get("/dispositivo", headers=_cabecera(self.emisor.token_usuario("u1")))
        self.assertEqual(r.status_code, 403)

    def test_token_de_dispositivo_aceptado_en_ruta_de_dispositivo(self):
        r = self.cliente.get("/dispositivo", headers=_cabecera(self.emisor.token_dispositivo("d1", "p1")))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"dispositivo_id": "d1", "planta_id": "p1"})

    def test_token_de_dispositivo_rechazado_en_ruta_de_usuario(self):
        r = self.cliente.get("/usuario", headers=_cabecera(self.emisor.token_dispositivo("d1", "p1")))
        self.assertEqual(r.status_code, 403)

    def test_token_expirado(self):
        ayer = datetime.now(timezone.utc) - timedelta(days=1)
        token = jwt.encode({"sub": "u1", "tipo": "usuario", "exp": ayer}, SECRETO, algorithm="HS256")
        r = self.cliente.get("/usuario", headers=_cabecera(token))
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.get_json(), {"error": "El token expiró"})

    def test_firmado_con_otro_secreto(self):
        token = EmisorJwt("otro-secreto-distinto-16+").token_usuario("u1")
        r = self.cliente.get("/usuario", headers=_cabecera(token))
        self.assertEqual(r.status_code, 401)

    def test_sin_cabecera(self):
        self.assertEqual(self.cliente.get("/usuario").status_code, 401)
        self.assertEqual(self.cliente.get("/dispositivo").status_code, 401)

    def test_dispositivo_con_alcance_incorrecto_es_rechazado(self):
        ahora = datetime.now(timezone.utc)
        token = jwt.encode(
            {"sub": "d1", "planta_id": "p1", "tipo": "dispositivo", "scope": "otro", "exp": ahora + timedelta(hours=1)},
            SECRETO, algorithm="HS256",
        )
        self.assertEqual(self.cliente.get("/dispositivo", headers=_cabecera(token)).status_code, 403)

    def test_el_secreto_esta_fijado_durante_la_prueba(self):
        # La clase de abajo comprueba que, fuera de las pruebas, el entorno queda como estaba
        self.assertEqual(os.environ["MATERA_JWT_SECRET"], SECRETO)


class TestEntornoRestaurado(unittest.TestCase):
    def test_el_secreto_de_la_prueba_no_queda_en_el_entorno(self):
        self.assertNotEqual(os.environ.get("MATERA_JWT_SECRET"), SECRETO)


if __name__ == "__main__":
    unittest.main()
