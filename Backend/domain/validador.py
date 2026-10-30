"""Regla central del dominio: comparar una lectura con el rango de su especie.

Es la logica de la fase 1, conservada (R1). No sabe de donde vino la lectura
(formulario, ESP32, manana MQTT) ni quien la va a leer despues.
"""

from domain.modelo import (
    NIVEL_BUENO,
    NIVEL_CRITICO,
    NIVEL_EXCELENTE,
    NIVEL_REGULAR,
    EstadoParametro,
    EvaluacionMatera,
    IndiceVitalidad,
    Lectura,
    RangoEspecie,
)

UMBRAL_EXCELENTE = 85.0
UMBRAL_BUENO = 70.0
UMBRAL_REGULAR = 50.0


class EvaluadorVitalidad:
    """Calcula el estado de cada parametro y el indice de vitalidad global.

    No depende de ningun puerto: recibe los dos datos que necesita y devuelve
    el resultado. Por eso se prueba sin dobles de prueba.
    """

    def evaluar(self, lectura: Lectura, rango: RangoEspecie) -> EvaluacionMatera:
        estado_humedad = self._estado(lectura.humedad, rango.humedad_min, rango.humedad_max)
        estado_luz = self._estado(lectura.luz, rango.luz_min, rango.luz_max)
        estado_temperatura = self._estado(lectura.temperatura, rango.temp_min, rango.temp_max)

        porcentaje = self._porcentaje(lectura, rango)
        todos_en_rango = all(
            estado is EstadoParametro.OPTIMO
            for estado in (estado_humedad, estado_luz, estado_temperatura)
        )

        return EvaluacionMatera(
            nombre_especie=rango.nombre_especie,
            lecturas=lectura,
            estado_humedad=estado_humedad,
            estado_luz=estado_luz,
            estado_temperatura=estado_temperatura,
            indice_vitalidad=IndiceVitalidad(
                porcentaje=porcentaje,
                nivel=self._nivel(porcentaje, todos_en_rango),
            ),
        )

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    def _estado(self, valor: float, minimo: float, maximo: float) -> EstadoParametro:
        if valor < minimo:
            return EstadoParametro.BAJO
        if valor > maximo:
            return EstadoParametro.ALTO
        return EstadoParametro.OPTIMO

    def _porcentaje(self, lectura: Lectura, rango: RangoEspecie) -> float:
        """Promedio de los tres puntajes. Cada variable pesa un tercio."""
        puntajes = (
            self._puntaje(lectura.humedad, rango.humedad_min, rango.humedad_max),
            self._puntaje(lectura.luz, rango.luz_min, rango.luz_max),
            self._puntaje(lectura.temperatura, rango.temp_min, rango.temp_max),
        )
        return round(sum(puntajes) / 3.0, 2)

    def _puntaje(self, valor: float, minimo: float, maximo: float) -> float:
        """Puntaje de 0 a 100 para un parametro.

        Dentro del rango ideal, 100. Fuera, decae segun la desviacion medida
        en anchos del propio rango: desviarse un rango completo da 0.

        Se mide contra el ancho del rango y no contra el valor del limite para
        que las tres variables se penalicen igual. Si se midiera contra el
        limite, 5000 lux de exceso sobre 20000 pesarian mucho menos que 5 C de
        exceso sobre 25, aunque las dos desviaciones sean igual de graves.
        """
        if minimo <= valor <= maximo:
            return 100.0

        amplitud = maximo - minimo
        if amplitud <= 0:
            amplitud = 1.0

        desviacion = (minimo - valor) if valor < minimo else (valor - maximo)
        return max(0.0, 1.0 - (desviacion / amplitud)) * 100.0

    def _nivel(self, porcentaje: float, todos_en_rango: bool) -> str:
        """EXCELENTE exige que los tres parametros esten en rango.

        Sin esa condicion el promedio disimula una desviacion: una orquidea a
        30 C con todo lo demas perfecto sacaba 93 % y se reportaba EXCELENTE.
        Cualquier parametro fuera de rango topa el nivel en BUENO.
        """
        if todos_en_rango:
            return NIVEL_EXCELENTE if porcentaje >= UMBRAL_EXCELENTE else NIVEL_BUENO
        if porcentaje >= UMBRAL_BUENO:
            return NIVEL_BUENO
        if porcentaje >= UMBRAL_REGULAR:
            return NIVEL_REGULAR
        return NIVEL_CRITICO
