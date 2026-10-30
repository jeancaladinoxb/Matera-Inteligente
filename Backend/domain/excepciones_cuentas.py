# PROVISIONAL (Julián, commit 0): simulación del contrato del dominio para poder desarrollar y probar
# los adaptadores mientras David implementa el dominio real. David puede reemplazar este archivo.
# Contrato: conservar nombres, campos y firmas. Sin lógica de negocio. Ver CONTRATOS.md.
from domain.excepciones import ExcepcionDominioBase


class PlantaNoEncontrada(ExcepcionDominioBase):
    def __init__(self, mensaje: str = "La planta no existe"):
        super().__init__(mensaje)


class SinLecturas(ExcepcionDominioBase):
    def __init__(self, mensaje: str = "La planta aún no tiene lecturas"):
        super().__init__(mensaje)


class UsuarioYaExiste(ExcepcionDominioBase):
    def __init__(self, mensaje: str = "Ya existe un usuario con ese correo"):
        super().__init__(mensaje)


class CredencialesInvalidas(ExcepcionDominioBase):
    def __init__(self, mensaje: str = "Credenciales inválidas"):
        super().__init__(mensaje)


class DatosInvalidos(ExcepcionDominioBase):
    def __init__(self, mensaje: str = "Datos inválidos"):
        super().__init__(mensaje)
