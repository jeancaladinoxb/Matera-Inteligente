from domain.entities import LecturaSensores, RangoEspecie, EvaluacionMatera
from domain.value_objects import EstadoParametro, IndiceVitalidad

# Principio de Responsabilidad Unica (SRP): Este servicio de dominio concentra unicamente la logica
# pura de negocio para evaluar las lecturas ambientales y calcular el indice de vitalidad de la planta.

# Principio Abierto/Cerrado (OCP): La logica de calculo esta encapsulada en este servicio.
# Permite modificar o extender las formulas de vitalidad sin alterar la estructura de las entidades ni del caso de uso.

class EvaluadorVitalidadService:
    """
    Servicio de dominio encargado del calculo del estado de cada parametro ambiental
    y de la determinacion del indice de vitalidad general de la planta.
    """

    def evaluar(self, lecturas: LecturaSensores, rango: RangoEspecie) -> EvaluacionMatera:
        """
        Evalua las lecturas de los sensores contra los rangos de la especie dada
        y genera un objeto EvaluacionMatera con los resultados.
        """
        estado_humedad = self._evaluar_parametro(
            lecturas.humedad, rango.humedad_min, rango.humedad_max
        )
        estado_luz = self._evaluar_parametro(
            lecturas.luz, rango.luz_min, rango.luz_max
        )
        estado_temp = self._evaluar_parametro(
            lecturas.temperatura, rango.temp_min, rango.temp_max
        )

        indice_vitalidad = self._calcular_indice_vitalidad(lecturas, rango)

        return EvaluacionMatera(
            nombre_especie=rango.nombre_especie,
            lecturas=lecturas,
            estado_humedad=estado_humedad,
            estado_luz=estado_luz,
            estado_temperatura=estado_temp,
            indice_vitalidad=indice_vitalidad
        )

    def _evaluar_parametro(self, valor: float, val_min: float, val_max: float) -> EstadoParametro:
        """
        Determina si un valor especifico se encuentra BAJO, OPTIMO o ALTO respecto a su rango ideal.
        """
        if valor < val_min:
            return EstadoParametro.BAJO
        elif valor > val_max:
            return EstadoParametro.ALTO
        else:
            return EstadoParametro.OPTIMO

    def _calcular_indice_vitalidad(self, lecturas: LecturaSensores, rango: RangoEspecie) -> IndiceVitalidad:
        """
        Calcula un porcentaje de vitalidad global (0 a 100%) promediando la salud de cada variable.
        """
        puntaje_humedad = self._calcular_puntaje_individual(lecturas.humedad, rango.humedad_min, rango.humedad_max)
        puntaje_luz = self._calcular_puntaje_individual(lecturas.luz, rango.luz_min, rango.luz_max)
        puntaje_temp = self._calcular_puntaje_individual(lecturas.temperatura, rango.temp_min, rango.temp_max)

        # Cada variable aporta un tercio del puntaje total
        porcentaje_total = round((puntaje_humedad + puntaje_luz + puntaje_temp) / 3.0, 2)

        # Determinacion del nivel cualitativo segun el porcentaje obtenido
        if porcentaje_total >= 85.0:
            nivel = "EXCELENTE"
        elif porcentaje_total >= 70.0:
            nivel = "BUENO"
        elif porcentaje_total >= 50.0:
            nivel = "REGULAR"
        else:
            nivel = "CRITICO"

        return IndiceVitalidad(porcentaje=porcentaje_total, nivel=nivel)

    def _calcular_puntaje_individual(self, valor: float, val_min: float, val_max: float) -> float:
        """
        Calcula un puntaje de 0 a 100 para un parametro individual.
        Si esta dentro del rango ideal obtiene 100 puntos.
        Si esta fuera, el puntaje decrece segun la desviacion relativa.
        """
        if val_min <= valor <= val_max:
            return 100.0

        if valor < val_min:
            diferencia = val_min - valor
            tolerancia = val_min if val_min > 0 else 1.0
            factor = max(0.0, 1.0 - (diferencia / tolerancia))
            return factor * 100.0

        # Caso valor > val_max
        diferencia = valor - val_max
        tolerancia = val_max if val_max > 0 else 1.0
        factor = max(0.0, 1.0 - (diferencia / tolerancia))
        return factor * 100.0
