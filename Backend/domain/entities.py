from dataclasses import dataclass
from domain.value_objects import EstadoParametro, IndiceVitalidad
from domain.excepciones import ValorFueraDeRangoFisicoError

# Principio de Responsabilidad Unica (SRP): Este archivo contiene unicamente la definicion de las entidades
# principales del dominio, las cuales representan el modelo del negocio de la matera inteligente.

@dataclass
class LecturaSensores:
    """
    Entidad/Objeto que agrupa las mediciones recolectadas por los sensores de la matera.
    Los limites fisicos razonables son:
    - Humedad: 0.0% a 100.0%
    - Luz: 0.0 lux a 150000.0 lux
    - Temperatura: -10.0 °C a 60.0 °C
    """
    humedad: float       # Porcentaje de humedad del sustrato (0 a 100%)
    luz: float           # Nivel de luz en lux (0 a 150000 lux)
    temperatura: float   # Temperatura ambiental en grados Celsius (-10 a 60 °C)

    def __post_init__(self):
        if not (0.0 <= self.humedad <= 100.0):
            raise ValorFueraDeRangoFisicoError("humedad", self.humedad, 0.0, 100.0, "%")
        if not (0.0 <= self.luz <= 150000.0):
            raise ValorFueraDeRangoFisicoError("luz", self.luz, 0.0, 150000.0, "lux")
        if not (-10.0 <= self.temperatura <= 60.0):
            raise ValorFueraDeRangoFisicoError("temperatura", self.temperatura, -10.0, 60.0, "°C")


@dataclass
class RangoEspecie:
    """
    Entidad que representa los rangos optimos de variables ambientales requeridos por una especie de planta.
    """
    nombre_especie: str
    humedad_min: float
    humedad_max: float
    luz_min: float
    luz_max: float
    temp_min: float
    temp_max: float

    def __post_init__(self):
        if self.humedad_min > self.humedad_max:
            raise ValueError("El rango de humedad minimo no puede ser mayor al maximo.")
        if self.luz_min > self.luz_max:
            raise ValueError("El rango de luz minimo no puede ser mayor al maximo.")
        if self.temp_min > self.temp_max:
            raise ValueError("El rango de temperatura minimo no puede ser mayor al maximo.")


@dataclass
class EvaluacionMatera:
    """
    Entidad que contiene el resultado consolidado del analisis de la matera para una especie determinada.
    """
    nombre_especie: str
    lecturas: LecturaSensores
    estado_humedad: EstadoParametro
    estado_luz: EstadoParametro
    estado_temperatura: EstadoParametro
    indice_vitalidad: IndiceVitalidad
