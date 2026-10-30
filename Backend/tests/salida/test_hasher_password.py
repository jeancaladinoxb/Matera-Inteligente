import unittest

from adaptadores.salida.hasher_password import HasherPassword


class TestHasherPassword(unittest.TestCase):
    def setUp(self):
        self.hasher = HasherPassword()

    def test_coincide_y_no_coincide(self):
        hash_ = self.hasher.hashear("clave-segura-123")
        self.assertTrue(self.hasher.coincide("clave-segura-123", hash_))
        self.assertFalse(self.hasher.coincide("otra-clave", hash_))
        self.assertFalse(self.hasher.coincide("", hash_))

    def test_el_hash_no_contiene_la_contrasena(self):
        self.assertNotIn("clave-segura-123", self.hasher.hashear("clave-segura-123"))

    def test_misma_contrasena_da_hashes_distintos(self):
        self.assertNotEqual(self.hasher.hashear("clave-segura-123"), self.hasher.hashear("clave-segura-123"))


if __name__ == "__main__":
    unittest.main()
