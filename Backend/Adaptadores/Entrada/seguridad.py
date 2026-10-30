import os
from functools import wraps
from typing import Any, Dict, Optional

import jwt
from flask import jsonify, request

# Deben coincidir con lo que emite emisor_jwt.py (acordar con C)
ALGORITMO = "HS256"
TIPO_USUARIO = "usuario"
TIPO_DISPOSITIVO = "dispositivo"
SCOPE_ESCRIBIR_LECTURAS = "lecturas:escribir"


class _TokenRechazado(Exception):
    def __init__(self, codigo: int, mensaje: str):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def _secreto() -> str:
    secreto = os.environ.get("MATERA_JWT_SECRET")
    if not secreto:
        # Fallar fuerte: nunca usar un secreto por defecto
        raise RuntimeError("Falta la variable de entorno MATERA_JWT_SECRET")
    return secreto


def _extraer_token() -> str:
    cabecera = request.headers.get("Authorization", "")
    partes = cabecera.split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise _TokenRechazado(401, "Falta el token o el formato es incorrecto")
    return partes[1]


def _decodificar(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            _secreto(),
            algorithms=[ALGORITMO],          # lista fija: evita ataques de algoritmo
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _TokenRechazado(401, "El token expiró")
    except jwt.InvalidTokenError:
        raise _TokenRechazado(401, "Token inválido")


def _rechazo(error: _TokenRechazado):
    return jsonify({"error": error.mensaje}), error.codigo


def usuario_requerido(vista):
    """Verifica un JWT de usuario e inyecta usuario_id (str) a la ruta."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        try:
            claims = _decodificar(_extraer_token())
            if claims.get("tipo") != TIPO_USUARIO:
                raise _TokenRechazado(403, "Este endpoint requiere un token de usuario")
        except _TokenRechazado as error:
            return _rechazo(error)
        return vista(*args, usuario_id=str(claims["sub"]), **kwargs)
    return envoltura


def dispositivo_requerido(vista):
    """Verifica un JWT de dispositivo e inyecta dispositivo_id y planta_id."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        try:
            claims = _decodificar(_extraer_token())
            if claims.get("tipo") != TIPO_DISPOSITIVO:
                raise _TokenRechazado(403, "Este endpoint requiere un token de dispositivo")
            if claims.get("scope") != SCOPE_ESCRIBIR_LECTURAS:
                raise _TokenRechazado(403, "El token no tiene el alcance necesario")
            planta_id: Optional[str] = claims.get("planta_id")
            if not planta_id:
                raise _TokenRechazado(401, "Token de dispositivo sin planta asociada")
        except _TokenRechazado as error:
            return _rechazo(error)
        return vista(
            *args,
            dispositivo_id=str(claims["sub"]),
            planta_id=str(planta_id),
            **kwargs,
        )
    return envoltura