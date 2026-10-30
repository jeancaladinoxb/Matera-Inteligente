"""Implementa UsuarioRepositorioPort en SQLite. Solo traduce filas <-> Usuario."""
import sqlite3
from pathlib import Path
from typing import Optional, Union

from adaptadores.salida.bd import conectar
from domain.excepciones_cuentas import UsuarioYaExiste
from domain.modelo import Usuario


def _normalizar(email: str) -> str:
    return email.strip().lower()


def _a_usuario(fila) -> Usuario:
    return Usuario(id=fila["id"], email=fila["email"], password_hash=fila["password_hash"])


class UsuarioRepositorioBd:
    def __init__(self, ruta_db: Union[str, Path]):
        self._ruta_db = ruta_db

    def guardar(self, usuario: Usuario) -> None:
        try:
            with conectar(self._ruta_db) as conexion:
                conexion.execute(
                    "INSERT INTO usuarios (id, email, password_hash) VALUES (?, ?, ?)",
                    (usuario.id, _normalizar(usuario.email), usuario.password_hash),
                )
        except sqlite3.IntegrityError as error:
            # Solo el correo repetido es UsuarioYaExiste; cualquier otro error de integridad se propaga
            if "usuarios.email" in str(error):
                raise UsuarioYaExiste() from None
            raise

    def por_email(self, email: str) -> Optional[Usuario]:
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT id, email, password_hash FROM usuarios WHERE email = ?", (_normalizar(email),)
            ).fetchone()
        return _a_usuario(fila) if fila else None

    def por_id(self, usuario_id: str) -> Optional[Usuario]:
        with conectar(self._ruta_db) as conexion:
            fila = conexion.execute(
                "SELECT id, email, password_hash FROM usuarios WHERE id = ?", (usuario_id,)
            ).fetchone()
        return _a_usuario(fila) if fila else None
