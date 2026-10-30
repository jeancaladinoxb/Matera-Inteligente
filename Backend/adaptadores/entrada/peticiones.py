from typing import Any, Dict

from flask import request

from adaptadores.entrada.errores import SolicitudInvalida


def cuerpo_json() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise SolicitudInvalida("El cuerpo debe ser un objeto JSON")
    return data


def texto(data: Dict[str, Any], campo: str) -> str:
    valor = data.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise SolicitudInvalida("Falta el campo '%s' o no es texto" % campo)
    return valor.strip()


def numero(data: Dict[str, Any], campo: str) -> float:
    valor = data.get(campo)
    # bool es subclase de int en Python, se excluye explícitamente
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise SolicitudInvalida("Falta el campo '%s' o no es numérico" % campo)
    return float(valor)