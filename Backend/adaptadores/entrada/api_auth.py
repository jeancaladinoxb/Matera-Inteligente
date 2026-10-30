"""Adaptador de entrada de cuentas: registro e inicio de sesión.

Son los dos únicos endpoints públicos. Solo traducen JSON a llamadas al puerto
y excepciones a códigos HTTP; el token lo emite el dominio pidiéndoselo a
EmisorTokenPort, no este archivo.
"""

from flask import Blueprint, jsonify

from adaptadores.entrada.peticiones import cuerpo_json, texto


def crear_blueprint_auth(autenticar) -> Blueprint:
    """autenticar: AutenticarUsuarioPort."""
    bp = Blueprint("api_auth", __name__)

    @bp.post("/api/auth/registro")
    def registro():
        data = cuerpo_json()
        usuario = autenticar.registrar(texto(data, "email"), texto(data, "password"))
        # Nunca se devuelve el hash de la contraseña.
        return jsonify({"usuario_id": usuario.id, "email": usuario.email}), 201

    @bp.post("/api/auth/login")
    def login():
        data = cuerpo_json()
        token = autenticar.iniciar_sesion(texto(data, "email"), texto(data, "password"))
        return jsonify({"token": token}), 200

    return bp
