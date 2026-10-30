"""Implementa EmisorTokenPort con PyJWT. Solo emite: la verificación es de adaptadores/entrada/seguridad.py."""
from datetime import datetime, timedelta, timezone

import jwt

from config import (
    JWT_ALG, JWT_EXP_DISPOSITIVO_DIAS, JWT_EXP_USUARIO_MIN, JWT_ISS,
    SCOPE_DISPOSITIVO, SCOPE_USUARIO, TIPO_DISPOSITIVO, TIPO_USUARIO,
)


class EmisorJwt:
    def __init__(self, secreto: str):
        self._secreto = secreto

    def token_usuario(self, usuario_id: str) -> str:
        return self._firmar(
            {"sub": usuario_id, "tipo": TIPO_USUARIO, "scope": SCOPE_USUARIO},
            timedelta(minutes=JWT_EXP_USUARIO_MIN),
        )

    def token_dispositivo(self, dispositivo_id: str, planta_id: str) -> str:
        return self._firmar(
            {"sub": dispositivo_id, "planta_id": planta_id, "tipo": TIPO_DISPOSITIVO, "scope": SCOPE_DISPOSITIVO},
            timedelta(days=JWT_EXP_DISPOSITIVO_DIAS),
        )

    def _firmar(self, claims: dict, duracion: timedelta) -> str:
        ahora = datetime.now(timezone.utc)
        claims = dict(claims, iss=JWT_ISS, iat=ahora, exp=ahora + duracion)
        return jwt.encode(claims, self._secreto, algorithm=JWT_ALG)   # PyJWT 2.x devuelve str
