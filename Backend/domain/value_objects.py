from enum import Enum
from dataclasses import dataclass

# Principio de Responsabilidad Unica (SRP): Este archivo define exclusivamente los Objetos de Valor (Value Objects)
# del dominio para garantizar que las mediciones y estados del sistema sean inmutables y consistentes.

class EstadoParametro(Enum):
    """
    Representa el estado individual de una variable ambiental respecto al rango optimo de la especie.
    """
    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"


@dataclass(frozen=True)
class IndiceVitalidad:
    """
    Representa el indice de vitalidad general calculado para la planta.
    Es un Objeto de Valor inmutable que agrupa el porcentaje y la categoria.
    """
    porcentaje: float  # Valor de 0.0 a 100.0
    nivel: str         # EXCELENTE, BUENO, REGULAR, CRITICO

    def __post_init__(self):
        # Validacion de rango en la construccion del Objeto de Valor
        if not (0.0 <= self.porcentaje <= 100.0):
            raise ValueError("El porcentaje de vitalidad debe estar entre 0.0 y 100.0")
