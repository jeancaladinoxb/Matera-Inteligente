import unittest

import jwt

import config
from adaptadores.salida.emisor_jwt import EmisorJwt

SECRETO = "secreto-de-prueba-de-16+"


class TestEmisorJwt(unittest.TestCase):
    def setUp(self):
        self.emisor = EmisorJwt(SECRETO)

    def _decodificar(self, token, secreto=SECRETO):
        return jwt.decode(token, secreto, algorithms=[config.JWT_ALG], issuer=config.JWT_ISS)

    def test_token_de_usuario(self):
        token = self.emisor.token_usuario("u1")
        self.assertIsInstance(token, str)
        claims = self._decodificar(token)
        self.assertEqual(claims["sub"], "u1")
        self.assertEqual(claims["tipo"], "usuario")
        self.assertEqual(claims["scope"], "usuario")
        self.assertEqual(claims["iss"], "matera")
        self.assertNotIn("planta_id", claims)
        self.assertEqual(claims["exp"] - claims["iat"], 60 * 60)

    def test_token_de_dispositivo(self):
        claims = self._decodificar(self.emisor.token_dispositivo("d1", "p1"))
        self.assertEqual(claims["sub"], "d1")
        self.assertEqual(claims["planta_id"], "p1")
        self.assertEqual(claims["tipo"], "dispositivo")
        self.assertEqual(claims["scope"], "lecturas:escribir")
        self.assertEqual(claims["iss"], "matera")
        self.assertEqual(claims["exp"] - claims["iat"], 365 * 24 * 60 * 60)

    def test_algoritmo_hs256(self):
        self.assertEqual(jwt.get_unverified_header(self.emisor.token_usuario("u1"))["alg"], "HS256")

    def test_otro_secreto_no_decodifica(self):
        token = self.emisor.token_usuario("u1")
        with self.assertRaises(jwt.InvalidSignatureError):
            self._decodificar(token, secreto="otro-secreto-distinto-16+")


if __name__ == "__main__":
    unittest.main()
