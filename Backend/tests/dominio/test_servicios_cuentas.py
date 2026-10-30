"""Pruebas de los servicios de cuentas con dobles en memoria: sin SQLite, sin archivos y sin JWT real."""
import unittest

from domain.excepciones import (
    DispositivoInactivo, DispositivoNoEncontrado, DispositivoYaVinculado, EspecieNoEncontradaError,
)
from domain.excepciones_cuentas import CredencialesInvalidas, DatosInvalidos, UsuarioYaExiste
from domain.modelo import Dispositivo, RangoEspecie
from domain.servicios_cuentas import AutenticarUsuarioServicio, VincularDispositivoServicio


class UsuariosEnMemoria:
    def __init__(self):
        self.por_email_ = {}

    def guardar(self, usuario):
        if usuario.email in self.por_email_:
            raise UsuarioYaExiste()
        self.por_email_[usuario.email] = usuario

    def por_email(self, email):
        return self.por_email_.get(email)

    def por_id(self, usuario_id):
        return next((u for u in self.por_email_.values() if u.id == usuario_id), None)


class HasherFalso:
    def hashear(self, password):
        return "hash(" + password[::-1] + ")"     # no es el texto en claro

    def coincide(self, password, password_hash):
        return password_hash == self.hashear(password)


class EmisorFalso:
    def token_usuario(self, usuario_id):
        return "token-usuario:" + usuario_id

    def token_dispositivo(self, dispositivo_id, planta_id):
        return "token-dispositivo:%s:%s" % (dispositivo_id, planta_id)


class PlantasEnMemoria:
    def __init__(self):
        self.guardadas = {}

    def guardar(self, planta):
        self.guardadas[planta.id] = planta

    def por_id(self, planta_id):
        return self.guardadas.get(planta_id)

    def de_usuario(self, usuario_id):
        return [p for p in self.guardadas.values() if p.usuario_id == usuario_id]


class DispositivosEnMemoria:
    def __init__(self, *dispositivos):
        self.guardados = {d.id: d for d in dispositivos}

    def guardar(self, dispositivo):
        self.guardados[dispositivo.id] = dispositivo

    def por_id(self, dispositivo_id):
        return self.guardados.get(dispositivo_id)

    def por_codigo(self, codigo):
        return next((d for d in self.guardados.values() if d.codigo_emparejamiento == codigo), None)


class TablaEnMemoria:
    def __init__(self):
        self.rangos = {"orquidea": RangoEspecie("Orquidea", 40, 70, 10000, 20000, 18, 25)}

    def por_especie(self, nombre):
        return self.rangos.get(nombre.strip().lower())

    def todas(self):
        return list(self.rangos.values())


class TestAutenticarUsuario(unittest.TestCase):
    def setUp(self):
        self.usuarios = UsuariosEnMemoria()
        self.servicio = AutenticarUsuarioServicio(self.usuarios, HasherFalso(), EmisorFalso())

    def test_registro_correcto(self):
        usuario = self.servicio.registrar("  Ana@Correo.CO ", "clave-12345")
        self.assertEqual(usuario.email, "ana@correo.co")
        self.assertTrue(usuario.id)
        self.assertNotIn("clave-12345", usuario.password_hash)
        self.assertIs(self.usuarios.por_email("ana@correo.co"), usuario)

    def test_registro_con_correo_duplicado(self):
        self.servicio.registrar("ana@correo.co", "clave-12345")
        with self.assertRaises(UsuarioYaExiste):
            self.servicio.registrar("ANA@correo.co", "otra-clave-123")

    def test_registro_con_datos_invalidos(self):
        for email, password in [("sin-arroba", "clave-12345"), ("@dominio.co", "clave-12345"),
                                ("ana@", "clave-12345"), ("", "clave-12345"), ("ana@correo.co", "corta"),
                                ("ana@correo.co", "1234567")]:
            with self.subTest(email=email, password=password):
                with self.assertRaises(DatosInvalidos):
                    self.servicio.registrar(email, password)
        self.assertEqual(self.usuarios.por_email_, {})

    def test_contrasena_de_ocho_caracteres_es_valida(self):
        self.servicio.registrar("ana@correo.co", "12345678")

    def test_login_correcto_devuelve_token(self):
        usuario = self.servicio.registrar("ana@correo.co", "clave-12345")
        self.assertEqual(self.servicio.iniciar_sesion(" ANA@correo.co", "clave-12345"), "token-usuario:" + usuario.id)

    def test_login_con_contrasena_mala_y_con_usuario_inexistente_dan_el_mismo_error(self):
        self.servicio.registrar("ana@correo.co", "clave-12345")
        with self.assertRaises(CredencialesInvalidas) as mala:
            self.servicio.iniciar_sesion("ana@correo.co", "equivocada-123")
        with self.assertRaises(CredencialesInvalidas) as inexistente:
            self.servicio.iniciar_sesion("nadie@correo.co", "clave-12345")
        self.assertIs(type(mala.exception), type(inexistente.exception))
        self.assertEqual(str(mala.exception), str(inexistente.exception))


class HasherContador(HasherFalso):
    """Cuenta cuántas veces se hashea y se compara."""

    def __init__(self):
        self.llamadas_hashear = 0
        self.llamadas_coincide = 0
        self.hashes_comparados = []

    def hashear(self, password):
        self.llamadas_hashear += 1
        return super().hashear(password)

    def coincide(self, password, password_hash):
        self.llamadas_coincide += 1
        self.hashes_comparados.append(password_hash)
        # Se llama a hashear del padre (no a self.hashear) para no contarlo como un hasheo más
        return HasherFalso.hashear(self, password) == password_hash


class TestIniciarSesionTiempoConstante(unittest.TestCase):
    def setUp(self):
        self.hasher = HasherContador()
        self.usuarios = UsuariosEnMemoria()
        self.servicio = AutenticarUsuarioServicio(self.usuarios, self.hasher, EmisorFalso())
        self.servicio.registrar("ana@correo.co", "clave-12345")
        self.hasher.llamadas_hashear = self.hasher.llamadas_coincide = 0
        self.hasher.hashes_comparados.clear()

    def test_el_hash_falso_se_calcula_una_sola_vez_en_el_constructor(self):
        hasher = HasherContador()
        servicio = AutenticarUsuarioServicio(UsuariosEnMemoria(), hasher, EmisorFalso())
        self.assertEqual(hasher.llamadas_hashear, 1)
        for _ in range(3):
            with self.assertRaises(CredencialesInvalidas):
                servicio.iniciar_sesion("nadie@correo.co", "clave-12345")
        self.assertEqual(hasher.llamadas_hashear, 1)

    def test_coincide_se_invoca_si_el_usuario_existe(self):
        with self.assertRaises(CredencialesInvalidas):
            self.servicio.iniciar_sesion("ana@correo.co", "equivocada-123")
        self.assertEqual(self.hasher.llamadas_coincide, 1)
        self.assertEqual(self.hasher.hashes_comparados, [self.usuarios.por_email("ana@correo.co").password_hash])

    def test_coincide_se_invoca_tambien_si_el_usuario_no_existe(self):
        with self.assertRaises(CredencialesInvalidas):
            self.servicio.iniciar_sesion("nadie@correo.co", "clave-12345")
        self.assertEqual(self.hasher.llamadas_coincide, 1)
        self.assertNotIn(self.usuarios.por_email("ana@correo.co").password_hash, self.hasher.hashes_comparados)

    def test_el_hash_falso_nunca_deja_entrar(self):
        # Aunque la contraseña sea la del hash falso (que nadie conoce), un usuario inexistente no inicia sesión
        with self.assertRaises(CredencialesInvalidas):
            self.servicio.iniciar_sesion("nadie@correo.co", "")
        self.assertEqual(self.servicio.iniciar_sesion("ana@correo.co", "clave-12345"), "token-usuario:" + self.usuarios.por_email("ana@correo.co").id)


class TestVincularDispositivo(unittest.TestCase):
    def setUp(self):
        self.plantas = PlantasEnMemoria()
        self.dispositivos = DispositivosEnMemoria(
            Dispositivo("d1", "ABCD2345", None, True),
            Dispositivo("d2", "WXYZ6789", "otra-planta", True),
            Dispositivo("d3", "INAC2222", None, False),
        )
        self.servicio = VincularDispositivoServicio(
            self.plantas, self.dispositivos, TablaEnMemoria(), EmisorFalso()
        )

    def test_vincular_correcto(self):
        r = self.servicio.vincular("u1", "Mi orquídea", "  ORQUIDEA ", "ABCD2345")
        planta = self.plantas.por_id(r.planta_id)
        self.assertEqual((planta.usuario_id, planta.nombre), ("u1", "Mi orquídea"))
        self.assertEqual(planta.especie, "Orquidea")                       # nombre canónico de la tabla
        self.assertEqual(self.dispositivos.por_id("d1").planta_id, r.planta_id)
        self.assertEqual(r.dispositivo_id, "d1")
        self.assertEqual(r.token_dispositivo, "token-dispositivo:d1:" + r.planta_id)

    def test_el_codigo_se_acepta_en_minusculas_y_con_espacios(self):
        self.assertEqual(self.servicio.vincular("u1", "P", "Orquidea", "  abcd2345 ").dispositivo_id, "d1")

    def test_codigo_inexistente(self):
        with self.assertRaises(DispositivoNoEncontrado):
            self.servicio.vincular("u1", "P", "Orquidea", "NOEXISTE")
        self.assertEqual(self.plantas.guardadas, {})

    def test_dispositivo_ya_vinculado(self):
        with self.assertRaises(DispositivoYaVinculado):
            self.servicio.vincular("u1", "P", "Orquidea", "WXYZ6789")

    def test_dispositivo_inactivo(self):
        with self.assertRaises(DispositivoInactivo):
            self.servicio.vincular("u1", "P", "Orquidea", "INAC2222")

    def test_especie_inexistente_no_crea_nada(self):
        with self.assertRaises(EspecieNoEncontradaError):
            self.servicio.vincular("u1", "P", "Baobab", "ABCD2345")
        self.assertEqual(self.plantas.guardadas, {})
        self.assertIsNone(self.dispositivos.por_id("d1").planta_id)

    def test_un_dispositivo_no_se_vincula_dos_veces(self):
        self.servicio.vincular("u1", "P", "Orquidea", "ABCD2345")
        with self.assertRaises(DispositivoYaVinculado):
            self.servicio.vincular("u2", "Q", "Orquidea", "ABCD2345")


if __name__ == "__main__":
    unittest.main()
