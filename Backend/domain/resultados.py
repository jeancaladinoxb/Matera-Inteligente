# PROVISIONAL (Julián, commit 0): simulación del contrato del dominio para poder desarrollar y probar
# los adaptadores mientras David implementa el dominio real. David puede reemplazar este archivo.
# Contrato: conservar nombres, campos y firmas. Sin lógica de negocio. Ver CONTRATOS.md.
from dataclasses import dataclass
from typing import Optional

from domain.modelo import EstadoPlanta


@dataclass
class ResultadoLectura:
    guardada: bool                       # False si la lectura ya existía (duplicada)
    estado: Optional[EstadoPlanta]


@dataclass
class PlantaVinculada:
    planta_id: str
    dispositivo_id: str
    token_dispositivo: str               # se entrega una sola vez
