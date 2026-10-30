# PROVISIONAL (Julián, commit 0): simulación del contrato del dominio para poder desarrollar y probar
# los adaptadores mientras David implementa el dominio real. David puede reemplazar este archivo.
# Contrato: conservar nombres, campos y firmas. Sin lógica de negocio. Ver CONTRATOS.md.
from typing import List, Protocol

from domain.comandos import RegistrarLecturaCmd
from domain.modelo import EstadoPlanta, EvaluacionMatera, Planta, RangoEspecie, Usuario
from domain.resultados import PlantaVinculada, ResultadoLectura


class RegistrarLecturaPort(Protocol):
    def registrar(self, cmd: RegistrarLecturaCmd) -> ResultadoLectura: ...


class EvaluarLecturaPort(Protocol):
    def evaluar(self, especie: str, humedad: float, luz: float, temperatura: float) -> EvaluacionMatera: ...


class ConsultarEstadoPort(Protocol):
    def consultar(self, usuario_id: str, planta_id: str) -> EstadoPlanta: ...


class ConsultarHistorialPort(Protocol):
    def historial(self, usuario_id: str, planta_id: str, limite: int) -> List[EstadoPlanta]: ...


class ListarPlantasPort(Protocol):
    def listar(self, usuario_id: str) -> List[Planta]: ...


class ListarEspeciesPort(Protocol):
    def listar(self) -> List[RangoEspecie]: ...


class VincularDispositivoPort(Protocol):
    def vincular(self, usuario_id: str, nombre: str, especie: str, codigo: str) -> PlantaVinculada: ...


class AutenticarUsuarioPort(Protocol):
    def registrar(self, email: str, password: str) -> Usuario: ...
    def iniciar_sesion(self, email: str, password: str) -> str: ...      # devuelve el JWT de usuario
