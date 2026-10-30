from types import SimpleNamespace

from domain.excepciones import LecturaInvalida


class FakeRegistrarLectura:
    """Simula RegistrarLecturaPort. Borrar cuando exista el dominio real."""

    def registrar(self, cmd):
        if not 0 <= cmd.humedad <= 100:
            raise LecturaInvalida("La humedad debe estar entre 0 y 100")
        return SimpleNamespace(planta_id="planta-1", vitalidad=100.0)