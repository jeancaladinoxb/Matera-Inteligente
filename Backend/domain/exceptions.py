# Principio de Responsabilidad Unica (SRP): Este archivo define exclusivamente las excepciones
# personalizadas del dominio para comunicar errores de las reglas de negocio de forma clara.

class ExcepcionDominioBase(Exception):
    """
    Excepcion base para todos los errores del dominio de la matera inteligente.
    """
    pass


class ValorFueraDeRangoFisicoError(ExcepcionDominioBase):
    """
    Excepcion lanzada cuando un parametro medido (humedad, luz, temperatura)
    supera los limites fisicamente posibles o razonables en el entorno real.
    """
    def __init__(self, campo: str, valor: float, limite_min: float, limite_max: float, unidad: str):
        self.campo = campo
        self.valor = valor
        self.limite_min = limite_min
        self.limite_max = limite_max
        self.unidad = unidad
        mensaje = (
            f"El valor {valor} {unidad} para el campo '{campo}' esta fuera del rango fisico razonable "
            f"[{limite_min} {unidad}, {limite_max} {unidad}]."
        )
        super().__init__(mensaje)


class EspecieNoEncontradaError(ExcepcionDominioBase):
    """
    Excepcion lanzada cuando una especie solicitada no existe en el repositorio de especies.
    """
    def __init__(self, nombre_especie: str):
        self.nombre_especie = nombre_especie
        mensaje = f"La especie '{nombre_especie}' no se encuentra registrada en el sistema."
        super().__init__(mensaje)
