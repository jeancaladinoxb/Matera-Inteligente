"""Batería de contrato de TablaReferenciaPort. Es un mixin (no una TestCase) para que cada
implementación la ejecute por separado: si pasan la misma batería, son intercambiables."""

NOMBRES_ESPERADOS = {"Orquidea", "Cactus", "Helecho", "Suculenta", "Ficus"}


class ContratoTablaReferencia:
    def crear_tabla(self):
        raise NotImplementedError

    def setUp(self):
        self.tabla = self.crear_tabla()

    def test_especie_existente(self):
        rango = self.tabla.por_especie("Orquidea")
        self.assertEqual(rango.nombre_especie, "Orquidea")
        self.assertEqual((rango.humedad_min, rango.humedad_max), (40.0, 70.0))
        self.assertEqual((rango.luz_min, rango.luz_max), (10000.0, 20000.0))
        self.assertEqual((rango.temp_min, rango.temp_max), (18.0, 25.0))

    def test_insensible_a_mayusculas_y_espacios(self):
        for texto in ("orquidea", "ORQUIDEA", "  Orquidea  ", "\tcactus\n"):
            with self.subTest(texto=texto):
                self.assertIsNotNone(self.tabla.por_especie(texto))

    def test_devuelve_el_nombre_canonico(self):
        self.assertEqual(self.tabla.por_especie("  cACTUS ").nombre_especie, "Cactus")

    def test_especie_inexistente(self):
        self.assertIsNone(self.tabla.por_especie("Baobab"))

    def test_vacio_o_solo_espacios(self):
        for texto in ("", "   "):
            with self.subTest(texto=texto):
                self.assertIsNone(self.tabla.por_especie(texto))

    def test_todas(self):
        todas = self.tabla.todas()
        self.assertEqual(len(todas), len(NOMBRES_ESPERADOS))
        self.assertEqual({r.nombre_especie for r in todas}, NOMBRES_ESPERADOS)
