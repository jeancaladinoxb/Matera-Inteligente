from flask import Flask, jsonify

from domain.excepciones import (
    AccesoDenegado, DispositivoInactivo, DispositivoNoEncontrado,
    DispositivoYaVinculado, LecturaInvalida,
)


class SolicitudInvalida(Exception):
    """Error de forma de la petición (campo faltante, tipo incorrecto)."""


_MAPA = [
    (SolicitudInvalida, 400),
    (LecturaInvalida, 400),
    (AccesoDenegado, 403),
    (DispositivoInactivo, 403),
    (DispositivoNoEncontrado, 404),
    (DispositivoYaVinculado, 409),
]


def registrar_manejadores(app: Flask) -> None:
    for excepcion, codigo in _MAPA:
        def _handler(error, codigo=codigo):
            return jsonify({"error": str(error)}), codigo
        app.register_error_handler(excepcion, _handler)

    @app.errorhandler(Exception)
    def _inesperado(error):
        app.logger.exception("Error no controlado")
        return jsonify({"error": "Error interno"}), 500