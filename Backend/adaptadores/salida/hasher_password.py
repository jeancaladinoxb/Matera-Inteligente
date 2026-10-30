"""Implementa HasherPasswordPort con werkzeug. Nunca guarda ni registra una contraseña en claro."""
from werkzeug.security import check_password_hash, generate_password_hash


class HasherPassword:
    def hashear(self, password: str) -> str:
        return generate_password_hash(password)

    def coincide(self, password: str, password_hash: str) -> bool:
        return check_password_hash(password_hash, password)
