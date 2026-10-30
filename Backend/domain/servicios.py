"""Casos de uso de lecturas y estado. Cada clase implementa un puerto de entrada.

Reciben los puertos de salida por constructor y nunca instancian un adaptador:
quien decide que implementacion se usa es app.py, el unico punto de composicion.

Los casos de uso de cuentas (registro, login, vinculacion) viven en
servicios_cuentas.py.
"""

from typing import List, Optional

from domain.comandos import RegistrarLecturaCmd
from domain.excepciones import (
    DispositivoNoEncontrado,
    EspecieNoEncontradaError,
)
from domain.excepciones_cuentas import PlantaNoEncontrada, SinLecturas
from domain.modelo import (
    EstadoPlanta,
    EvaluacionMatera,
    Lectura,
    Planta,
    RangoEspecie,
    ahora,
    especies_ordenadas,
)
from domain.puertos.salida import (
    DispositivoRepositorioPort,
    HistorialLecturasPort,
    PlantaRepositorioPort,
    TablaReferenciaPort,
)
from domain.resultados import ResultadoLectura
from domain.validador import EvaluadorVitalidad

LIMITE_HISTORIAL_MAXIMO = 200

# Un dispositivo "vacio" para la evaluacion manual de la fase 1: ahi no hay
# ESP32 ninguno y la lectura no se guarda.
SIN_DISPOSITIVO = ""


# --------------------------------------------------------------------------
# R1: la validacion de la fase 1, ahora detras de un puerto
# --------------------------------------------------------------------------

class EvaluarLecturaServicio:
    """Implementa EvaluarLecturaPort. No guarda nada."""

    def __init__(self, tabla: TablaReferenciaPort, evaluador: Optional[EvaluadorVitalidad] = None):
        self._tabla = tabla
        self._evaluador = evaluador or EvaluadorVitalidad()

    def evaluar(
        self, especie: str, humedad: float, luz: float, temperatura: float
    ) -> EvaluacionMatera:
        rango = self._tabla.por_especie(especie)
        if rango is None:
            raise EspecieNoEncontradaError(especie)

        # Construir la Lectura valida los limites fisicos.
        lectura = Lectura(
            dispositivo_id=SIN_DISPOSITIVO,
            marca_tiempo=ahora(),
            humedad=humedad,
            luz=luz,
            temperatura=temperatura,
        )
        return self._evaluador.evaluar(lectura, rango)


class ListarEspeciesServicio:
    """Implementa ListarEspeciesPort."""

    def __init__(self, tabla: TablaReferenciaPort):
        self._tabla = tabla

    def listar(self) -> List[RangoEspecie]:
        return especies_ordenadas(self._tabla.todas())


# --------------------------------------------------------------------------
# R2 y R5: lecturas que llegan del dispositivo
# --------------------------------------------------------------------------

class RegistrarLecturaServicio:
    """Implementa RegistrarLecturaPort.

    El dispositivo solo reporta numeros. Quien es su dueno y que especie tiene
    la planta sale del repositorio, nunca del mensaje: por eso un token robado
    no sirve para escribir en otra planta ni para mentir sobre la especie.
    """

    def __init__(
        self,
        tabla: TablaReferenciaPort,
        historial: HistorialLecturasPort,
        plantas: PlantaRepositorioPort,
        dispositivos: DispositivoRepositorioPort,
        evaluador: Optional[EvaluadorVitalidad] = None,
    ):
        self._tabla = tabla
        self._historial = historial
        self._plantas = plantas
        self._dispositivos = dispositivos
        self._evaluador = evaluador or EvaluadorVitalidad()

    def registrar(self, cmd: RegistrarLecturaCmd) -> ResultadoLectura:
        dispositivo = self._dispositivos.por_id(cmd.dispositivo_id)
        if dispositivo is None:
            raise DispositivoNoEncontrado("No existe un dispositivo con ese id")

        # Revocacion antes que datos: un dispositivo desvinculado no escribe
        # aunque su token siga sin expirar.
        dispositivo.verificar_activo()

        if not dispositivo.esta_vinculado():
            raise PlantaNoEncontrada("El dispositivo no esta vinculado a ninguna planta")

        planta = self._plantas.por_id(dispositivo.planta_id)
        if planta is None:
            raise PlantaNoEncontrada("La planta del dispositivo no existe")

        rango = self._tabla.por_especie(planta.especie)
        if rango is None:
            raise EspecieNoEncontradaError(planta.especie)

        # Construir la Lectura valida los limites fisicos: humedad 140 o un
        # texto en lugar de un numero mueren aqui, antes de tocar el historial.
        lectura = Lectura(
            dispositivo_id=dispositivo.id,
            marca_tiempo=cmd.marca_tiempo,
            humedad=cmd.humedad,
            luz=cmd.luz,
            temperatura=cmd.temperatura,
        )

        evaluacion = self._evaluador.evaluar(lectura, rango)

        # Si la lectura estaba repetida el historial devuelve False y no
        # guarda. El estado que se devuelve es el mismo, para que un reenvio
        # del dispositivo sea inofensivo.
        guardada = self._historial.guardar(planta.id, lectura, evaluacion)

        return ResultadoLectura(
            guardada=guardada,
            estado=EstadoPlanta(planta_id=planta.id, lectura=lectura, evaluacion=evaluacion),
        )


# --------------------------------------------------------------------------
# R6 y R7: lo que consulta el usuario
# --------------------------------------------------------------------------

class ConsultarEstadoServicio:
    """Implementa ConsultarEstadoPort."""

    def __init__(self, plantas: PlantaRepositorioPort, historial: HistorialLecturasPort):
        self._plantas = plantas
        self._historial = historial

    def consultar(self, usuario_id: str, planta_id: str) -> EstadoPlanta:
        planta = _exigir_planta_propia(self._plantas, usuario_id, planta_id)

        estado = self._historial.ultima(planta.id)
        if estado is None:
            raise SinLecturas()
        return estado


class ConsultarHistorialServicio:
    """Implementa ConsultarHistorialPort."""

    def __init__(self, plantas: PlantaRepositorioPort, historial: HistorialLecturasPort):
        self._plantas = plantas
        self._historial = historial

    def historial(self, usuario_id: str, planta_id: str, limite: int) -> List[EstadoPlanta]:
        planta = _exigir_planta_propia(self._plantas, usuario_id, planta_id)
        return self._historial.historial(planta.id, max(1, min(int(limite), LIMITE_HISTORIAL_MAXIMO)))


class ListarPlantasServicio:
    """Implementa ListarPlantasPort.

    Aqui la regla de propiedad se cumple filtrando en origen: el repositorio
    solo devuelve las plantas de ese usuario, asi que no hay nada que negar.
    """

    def __init__(self, plantas: PlantaRepositorioPort):
        self._plantas = plantas

    def listar(self, usuario_id: str) -> List[Planta]:
        return self._plantas.de_usuario(usuario_id)


def _exigir_planta_propia(
    plantas: PlantaRepositorioPort, usuario_id: str, planta_id: str
) -> Planta:
    """Existe y es tuya, o no sigues. Es la regla R7 del enunciado."""
    planta = plantas.por_id(planta_id)
    if planta is None:
        raise PlantaNoEncontrada()
    planta.verificar_dueno(usuario_id)
    return planta
