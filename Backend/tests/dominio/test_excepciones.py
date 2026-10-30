# PROVISIONAL (Julián, commit 0): prueba corta del contrato de excepciones del dominio.
import inspect
import unittest

from domain import excepciones, excepciones_cuentas
from domain.excepciones import (
    AccesoDenegado, DispositivoInactivo, DispositivoNoEncontrado, DispositivoYaVinculado,
    EspecieNoEncontradaError, ExcepcionDominioBase, LecturaInvalida, ValorFueraDeRangoFisicoError,
)
from domain.excepciones_cuentas import (
    CredencialesInvalidas, DatosInvalidos, PlantaNoEncontrada, SinLecturas, UsuarioYaExiste,
)

NUEVAS = [PlantaNoEncontrada, SinLecturas, UsuarioYaExiste, CredencialesInvalidas, DatosInvalidos]
EXISTENTES = [
    ValorFueraDeRangoFisicoError, EspecieNoEncontradaError, LecturaInvalida, AccesoDenegado,
    DispositivoInactivo, DispositivoNoEncontrado, DispositivoYaVinculado,
]


class TestExcepciones(unittest.TestCase):
    def test_todas_heredan_de_la_base(self):
        for clase in NUEVAS + EXISTENTES:
            with self.subTest(clase=clase.__name__):
                self.assertTrue(issubclass(clase, ExcepcionDominioBase))

    def test_nuevas_tienen_mensaje_por_defecto(self):
        for clase in NUEVAS:
            with self.subTest(clase=clase.__name__):
                self.assertTrue(str(clase()))

    def test_firmas_de_la_fase_1_se_conservan(self):
        firma = lambda c: list(inspect.signature(c.__init__).parameters)[1:]
        self.assertEqual(
            firma(ValorFueraDeRangoFisicoError),
            ["campo", "valor", "limite_min", "limite_max", "unidad"],
        )
        self.assertEqual(firma(EspecieNoEncontradaError), ["nombre_especie"])

    def test_los_dos_modulos_no_se_pisan_nombres(self):
        propios = {n for n in vars(excepciones_cuentas) if n[0].isupper()} - {"ExcepcionDominioBase"}
        self.assertFalse(propios & {n for n in vars(excepciones) if n[0].isupper()})


if __name__ == "__main__":
    unittest.main()
