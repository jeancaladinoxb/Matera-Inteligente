from dataclasses import dataclass
from typing import Dict, Any, Optional

# Principio de Responsabilidad Unica (SRP): Este archivo contiene los Objetos de Transferencia de Datos (DTO)
# encargados de desacoplar los datos internos del dominio de los datos transferidos hacia/desde la capa de presentacion.

@dataclass
class EvaluacionRequestDTO:
    """
    Estructura de datos enviada por la capa de presentacion para solicitar la evaluacion de una matera.
    """
    especie: str
    humedad: float
    luz: float
    temperatura: float


@dataclass
class EvaluacionResponseDTO:
    """
    Estructura de respuesta serializable lista para ser entregada a la capa de presentacion (Flask / JSON).
    """
    exito: bool
    mensaje: str
    especie: str
    humedad_medida: float
    luz_medida: float
    temperatura_medida: float
    estado_humedad: Optional[str]
    estado_luz: Optional[str]
    estado_temperatura: Optional[str]
    porcentaje_vitalidad: Optional[float]
    nivel_vitalidad: Optional[str]

    def a_diccionario(self) -> Dict[str, Any]:
        """
        Convierte la respuesta a un diccionario para ser retornado por Flask en formato JSON.
        """
        return {
            "exito": self.exito,
            "mensaje": self.mensaje,
            "especie": self.especie,
            "lecturas": {
                "humedad": self.humedad_medida,
                "luz": self.luz_medida,
                "temperatura": self.temperatura_medida
            },
            "estados": {
                "humedad": self.estado_humedad,
                "luz": self.estado_luz,
                "temperatura": self.estado_temperatura
            },
            "vitalidad": {
                "porcentaje": self.porcentaje_vitalidad,
                "nivel": self.nivel_vitalidad
            }
        }
