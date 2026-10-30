"""Prueba de extremo a extremo: la aplicacion real, sin dobles.

Levanta create_app() contra una base de datos temporal y recorre el flujo
completo del enunciado: registro, login, vinculacion, lecturas del dispositivo
y consulta del estado, incluyendo los casos de error de la sustentacion.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from adaptadores.salida.tabla_bd import cargar_especies
from adaptadores.salida.tabla_csv import TablaReferenciaCsv
from app import create_app
from config import RUTA_CSV_POR_DEFECTO, Config
from scripts.cargar_datos import crear_dispositivos

SECRETO = "secreto-de-prueba-bien-largo-123"


class TestExtremoAExtremo(unittest.TestCase):

    TABLA = "csv"

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta_db = os.path.join(self.directorio.name, "matera.db")

        self.cfg = Config(
            tabla=self.TABLA,
            ruta_csv=RUTA_CSV_POR_DEFECTO,
            ruta_db=self.ruta_db,
            jwt_secret=SECRETO,
            cors_origins=["http://localhost:5500"],
        )
        os.environ["MATERA_JWT_SECRET"] = SECRETO   # lo lee seguridad.py

        self.app = create_app(self.cfg)
        self.cliente = self.app.test_client()

        # Semilla: la tabla de especies en BD y un dispositivo de fabrica.
        cargar_especies(self.ruta_db, TablaReferenciaCsv(RUTA_CSV_POR_DEFECTO).todas())
        crear_dispositivos(self.ruta_db, 1)
        self.codigo = self._primer_codigo()

    def tearDown(self):
        self.directorio.cleanup()

    # ------------------------------------------------------------------

    def _primer_codigo(self):
        from adaptadores.salida.bd import conectar

        with conectar(self.ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT codigo_emparejamiento FROM dispositivos LIMIT 1"
            ).fetchone()
        return fila["codigo_emparejamiento"]

    def _pedir(self, metodo, ruta, token=None, cuerpo=None):
        cabeceras = {}
        if token:
            cabeceras["Authorization"] = "Bearer " + token
        kwargs = {"headers": cabeceras}
        if cuerpo is not None:
            kwargs["data"] = json.dumps(cuerpo)
            kwargs["content_type"] = "application/json"
        return getattr(self.cliente, metodo)(ruta, **kwargs)

    def _usuario(self, email="david@matera.co", password="claveSegura1"):
        self._pedir("post", "/api/auth/registro", cuerpo={"email": email, "password": password})
        r = self._pedir("post", "/api/auth/login", cuerpo={"email": email, "password": password})
        self.assertEqual(r.status_code, 200)
        return r.get_json()["token"]

    def _vincular(self, token):
        r = self._pedir("post", "/api/plantas", token, {
            "nombre": "Orquidea de la sala", "especie": "Orquidea", "codigo": self.codigo,
        })
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        return r.get_json()

    def _lectura(self, segundos=0, **campos):
        cuerpo = {
            "marca_tiempo": (datetime(2026, 10, 30, tzinfo=timezone.utc)
                             + timedelta(seconds=segundos)).isoformat(),
            "humedad": 50.0, "luz": 15000.0, "temperatura": 20.0,
        }
        cuerpo.update(campos)
        return cuerpo

    # ------------------------------------------------------------------

    def test_flujo_completo(self):
        token = self._usuario()

        especies = self._pedir("get", "/api/especies", token)
        self.assertEqual(especies.status_code, 200)
        self.assertIn("rangos", especies.get_json()[0])

        vinculada = self._vincular(token)
        planta_id = vinculada["planta_id"]
        token_dispositivo = vinculada["token_dispositivo"]

        plantas = self._pedir("get", "/api/plantas", token).get_json()
        self.assertEqual([p["planta_id"] for p in plantas], [planta_id])

        r = self._pedir("post", "/api/dispositivos/%s/lecturas" % vinculada["dispositivo_id"],
                        token_dispositivo, self._lectura())
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        self.assertEqual(r.get_json()["vitalidad"]["nivel"], "EXCELENTE")

        estado = self._pedir("get", "/api/plantas/%s/estado" % planta_id, token)
        self.assertEqual(estado.status_code, 200)
        cuerpo = estado.get_json()
        self.assertEqual(cuerpo["especie"], "Orquidea")
        self.assertEqual(cuerpo["estados"]["humedad"], "OPTIMO")
        self.assertEqual(cuerpo["vitalidad"]["porcentaje"], 100.0)

        historial = self._pedir("get", "/api/plantas/%s/historial" % planta_id, token)
        self.assertEqual(historial.status_code, 200)
        self.assertEqual(len(historial.get_json()), 1)

    def test_evaluacion_manual_r1(self):
        token = self._usuario()
        r = self._pedir("post", "/api/evaluar", token, {
            "especie": "Orquidea", "humedad": 50.0, "luz": 15000.0, "temperatura": 20.0,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["vitalidad"]["nivel"], "EXCELENTE")

    def test_lectura_fuera_de_rango_se_guarda_y_no_es_excelente(self):
        token = self._usuario()
        v = self._vincular(token)
        r = self._pedir("post", "/api/dispositivos/%s/lecturas" % v["dispositivo_id"],
                        v["token_dispositivo"], self._lectura(temperatura=30.0))
        self.assertEqual(r.status_code, 201)
        self.assertNotEqual(r.get_json()["vitalidad"]["nivel"], "EXCELENTE")

        estado = self._pedir("get", "/api/plantas/%s/estado" % v["planta_id"], token).get_json()
        self.assertEqual(estado["estados"]["temperatura"], "ALTO")

    def test_lecturas_invalidas_dan_400_y_no_se_guardan(self):
        token = self._usuario()
        v = self._vincular(token)
        ruta = "/api/dispositivos/%s/lecturas" % v["dispositivo_id"]

        for descripcion, cuerpo in [
            ("humedad imposible", self._lectura(humedad=140.0)),
            ("texto en vez de numero", self._lectura(humedad="mucha")),
            ("fecha mal formada", self._lectura(marca_tiempo="ayer por la tarde")),
        ]:
            with self.subTest(caso=descripcion):
                r = self._pedir("post", ruta, v["token_dispositivo"], cuerpo)
                self.assertEqual(r.status_code, 400, r.get_data(as_text=True))

        falta_campo = self._lectura()
        del falta_campo["luz"]
        self.assertEqual(self._pedir("post", ruta, v["token_dispositivo"], falta_campo).status_code, 400)

        estado = self._pedir("get", "/api/plantas/%s/estado" % v["planta_id"], token)
        self.assertEqual(estado.status_code, 404, "no debia haber quedado ninguna lectura")

    def test_lectura_repetida_no_se_duplica(self):
        token = self._usuario()
        v = self._vincular(token)
        ruta = "/api/dispositivos/%s/lecturas" % v["dispositivo_id"]

        self.assertEqual(self._pedir("post", ruta, v["token_dispositivo"], self._lectura()).status_code, 201)
        repetida = self._pedir("post", ruta, v["token_dispositivo"], self._lectura())
        self.assertEqual(repetida.status_code, 200)
        self.assertFalse(repetida.get_json()["guardada"])

        historial = self._pedir("get", "/api/plantas/%s/historial" % v["planta_id"], token)
        self.assertEqual(len(historial.get_json()), 1)

    def test_planta_ajena_da_403(self):
        token = self._usuario()
        v = self._vincular(token)
        self._pedir("post", "/api/dispositivos/%s/lecturas" % v["dispositivo_id"],
                    v["token_dispositivo"], self._lectura())

        intruso = self._usuario("intruso@matera.co", "otraClave123")
        for ruta in ("estado", "historial"):
            with self.subTest(ruta=ruta):
                r = self._pedir("get", "/api/plantas/%s/%s" % (v["planta_id"], ruta), intruso)
                self.assertEqual(r.status_code, 403)

    def test_tokens_cruzados_y_ausentes(self):
        token = self._usuario()
        v = self._vincular(token)
        ruta = "/api/dispositivos/%s/lecturas" % v["dispositivo_id"]

        self.assertEqual(self._pedir("get", "/api/plantas").status_code, 401)
        self.assertEqual(self._pedir("get", "/api/plantas", "esto.no.es.un.jwt").status_code, 401)
        # token de usuario en el endpoint del dispositivo
        self.assertEqual(self._pedir("post", ruta, token, self._lectura()).status_code, 403)
        # token de dispositivo en un endpoint de usuario
        self.assertEqual(self._pedir("get", "/api/plantas", v["token_dispositivo"]).status_code, 403)
        # el dispositivo reporta a nombre de otro
        otro = "/api/dispositivos/d-999/lecturas"
        self.assertEqual(self._pedir("post", otro, v["token_dispositivo"], self._lectura()).status_code, 403)

    def test_un_codigo_no_se_puede_reclamar_dos_veces(self):
        self._vincular(self._usuario())
        otro = self._usuario("otro@matera.co", "otraClave123")
        r = self._pedir("post", "/api/plantas", otro, {
            "nombre": "La mia", "especie": "Cactus", "codigo": self.codigo,
        })
        self.assertEqual(r.status_code, 409)

    def test_correo_repetido_da_409(self):
        self._usuario()
        r = self._pedir("post", "/api/auth/registro",
                        cuerpo={"email": "david@matera.co", "password": "claveSegura1"})
        self.assertEqual(r.status_code, 409)

    def test_credenciales_malas_dan_401(self):
        self._usuario()
        r = self._pedir("post", "/api/auth/login",
                        cuerpo={"email": "david@matera.co", "password": "equivocada1"})
        self.assertEqual(r.status_code, 401)


class TestExtremoAExtremoConBd(TestExtremoAExtremo):
    """El mismo recorrido con MATERA_TABLA=bd.

    Es la prueba de cambio del enunciado: cambiar la fuente de los rangos no
    altera ni una respuesta. Si esta clase pasa, la demo de CSV <-> BD funciona.
    """

    TABLA = "bd"


if __name__ == "__main__":
    unittest.main()
