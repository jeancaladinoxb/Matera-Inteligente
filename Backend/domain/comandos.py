from dataclasses import dataclass
from datetime import datetime


@dataclass
class RegistrarLecturaCmd:
    dispositivo_id: str
    marca_tiempo: datetime
    humedad: float
    luz: float
    temperatura: float