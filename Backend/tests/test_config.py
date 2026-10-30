import os
import unittest
from unittest.mock import patch

import config
from config import ErrorConfiguracion, cargar_config

SECRETO = "s" * 20


class TestCargarConfig(unittest.TestCase):
    def test_valores_por_defecto(self):
        cfg = cargar_config({"MATERA_JWT_SECRET": SECRETO})
        self.assertEqual(cfg.tabla, "csv")
        self.assertEqual(cfg.ruta_db, "matera.db")
        self.assertTrue(cfg.ruta_csv.endswith(os.path.join("infrastructure", "especies.csv")))
        self.assertEqual(cfg.cors_origins, [])
        self.assertEqual(cfg.jwt_secret, SECRETO)

    def test_lee_todas_las_variables(self):
        cfg = cargar_config({
            "MATERA_TABLA": "BD", "MATERA_CSV": "otro.csv", "MATERA_DB": "otra.db",
            "MATERA_JWT_SECRET": SECRETO,
            "MATERA_CORS_ORIGINS": " http://a.com , http://b.com,,",
        })
        self.assertEqual(cfg.tabla, "bd")
        self.assertEqual(cfg.ruta_csv, "otro.csv")
        self.assertEqual(cfg.ruta_db, "otra.db")
        self.assertEqual(cfg.cors_origins, ["http://a.com", "http://b.com"])

    def test_tabla_invalida(self):
        with self.assertRaises(ErrorConfiguracion) as ctx:
            cargar_config({"MATERA_TABLA": "mongo", "MATERA_JWT_SECRET": SECRETO})
        self.assertIn("MATERA_TABLA", str(ctx.exception))

    def test_secreto_ausente_o_corto(self):
        for env in ({}, {"MATERA_JWT_SECRET": ""}, {"MATERA_JWT_SECRET": "corto"}):
            with self.subTest(env=env):
                with self.assertRaises(ErrorConfiguracion):
                    cargar_config(env)

    def test_el_mensaje_de_error_no_revela_el_secreto(self):
        with self.assertRaises(ErrorConfiguracion) as ctx:
            cargar_config({"MATERA_JWT_SECRET": "corto-secreto"})
        self.assertNotIn("corto-secreto", str(ctx.exception))


class TestSinEfectosSecundarios(unittest.TestCase):
    def test_con_diccionario_no_carga_dotenv_ni_toca_os_environ(self):
        antes = dict(os.environ)
        with patch.object(config, "load_dotenv") as dotenv:
            cargar_config({"MATERA_JWT_SECRET": SECRETO, "MATERA_DB": "x.db"})
        dotenv.assert_not_called()
        self.assertEqual(dict(os.environ), antes)

    def test_con_os_environ_si_carga_dotenv(self):
        with patch.dict(os.environ, {"MATERA_JWT_SECRET": SECRETO}):
            with patch.object(config, "load_dotenv") as dotenv:
                cfg = cargar_config()
            dotenv.assert_called_once_with()
            self.assertEqual(cfg.jwt_secret, SECRETO)

    def test_sin_python_dotenv_usa_solo_os_environ(self):
        with patch.dict(os.environ, {"MATERA_JWT_SECRET": SECRETO}):
            with patch.object(config, "load_dotenv", None):
                self.assertEqual(cargar_config().jwt_secret, SECRETO)


class TestConstantesJwt(unittest.TestCase):
    def test_coinciden_con_seguridad_py(self):
        from adaptadores.entrada import seguridad
        self.assertEqual(config.JWT_ALG, seguridad.ALGORITMO)
        self.assertEqual(config.TIPO_USUARIO, seguridad.TIPO_USUARIO)
        self.assertEqual(config.TIPO_DISPOSITIVO, seguridad.TIPO_DISPOSITIVO)
        self.assertEqual(config.SCOPE_DISPOSITIVO, seguridad.SCOPE_ESCRIBIR_LECTURAS)


if __name__ == "__main__":
    unittest.main()
