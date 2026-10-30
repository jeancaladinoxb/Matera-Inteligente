"""Casos de uso de cuentas: registro, inicio de sesión y vinculación de dispositivos.

Solo conoce puertos y modelo: no sabe si los datos viven en SQLite ni cómo se firma un token.
"""
import uuid

from domain.excepciones import (
    DispositivoInactivo, DispositivoNoEncontrado, DispositivoYaVinculado, EspecieNoEncontradaError,
)
from domain.excepciones_cuentas import CredencialesInvalidas, DatosInvalidos
from domain.modelo import Planta, Usuario
from domain.puertos.salida import (
    DispositivoRepositorioPort, EmisorTokenPort, HasherPasswordPort, PlantaRepositorioPort,
    TablaReferenciaPort, UsuarioRepositorioPort,
)
from domain.resultados import PlantaVinculada

LARGO_MINIMO_PASSWORD = 8


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


class AutenticarUsuarioServicio:
    """Implementa AutenticarUsuarioPort."""

    def __init__(self, usuarios: UsuarioRepositorioPort, hasher: HasherPasswordPort, emisor: EmisorTokenPort):
        self._usuarios = usuarios
        self._hasher = hasher
        self._emisor = emisor

    def registrar(self, email: str, password: str) -> Usuario:
        email = _normalizar_email(email)
        local, arroba, dominio = email.partition("@")
        if not (local and arroba and dominio):
            raise DatosInvalidos("El correo no tiene un formato válido")
        if len(password) < LARGO_MINIMO_PASSWORD:
            raise DatosInvalidos("La contraseña debe tener al menos %d caracteres" % LARGO_MINIMO_PASSWORD)
        usuario = Usuario(id=uuid.uuid4().hex, email=email, password_hash=self._hasher.hashear(password))
        self._usuarios.guardar(usuario)   # el repositorio lanza UsuarioYaExiste si el correo ya está
        return usuario

    def iniciar_sesion(self, email: str, password: str) -> str:
        usuario = self._usuarios.por_email(_normalizar_email(email))
        # El mismo error si el usuario no existe o la contraseña es mala: no se revela qué correos existen
        if usuario is None or not self._hasher.coincide(password, usuario.password_hash):
            raise CredencialesInvalidas()
        return self._emisor.token_usuario(usuario.id)


class VincularDispositivoServicio:
    """Implementa VincularDispositivoPort."""

    def __init__(
        self,
        plantas: PlantaRepositorioPort,
        dispositivos: DispositivoRepositorioPort,
        tabla: TablaReferenciaPort,
        emisor: EmisorTokenPort,
    ):
        self._plantas = plantas
        self._dispositivos = dispositivos
        self._tabla = tabla
        self._emisor = emisor

    def vincular(self, usuario_id: str, nombre: str, especie: str, codigo: str) -> PlantaVinculada:
        # Los códigos son mayúsculas y dígitos: se tolera que el usuario los escriba en minúsculas
        dispositivo = self._dispositivos.por_codigo(codigo.strip().upper())
        if dispositivo is None:
            raise DispositivoNoEncontrado("No existe un dispositivo con ese código")
        if dispositivo.planta_id is not None:
            raise DispositivoYaVinculado("El dispositivo ya está vinculado a una planta")
        if not dispositivo.activo:
            raise DispositivoInactivo("El dispositivo está inactivo")

        rango = self._tabla.por_especie(especie)
        if rango is None:
            raise EspecieNoEncontradaError(especie)

        planta = Planta(id=uuid.uuid4().hex, usuario_id=usuario_id, nombre=nombre, especie=rango.nombre_especie)
        self._plantas.guardar(planta)
        dispositivo.planta_id = planta.id
        self._dispositivos.guardar(dispositivo)

        # El token se entrega una sola vez, en esta respuesta
        token = self._emisor.token_dispositivo(dispositivo.id, planta.id)
        return PlantaVinculada(planta_id=planta.id, dispositivo_id=dispositivo.id, token_dispositivo=token)
