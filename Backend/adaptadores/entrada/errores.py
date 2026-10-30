from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from domain.excepciones import (
    AccesoDenegado, DispositivoInactivo, DispositivoNoEncontrado,
    DispositivoYaVinculado, EspecieNoEncontradaError, LecturaInvalida,
    ValorFueraDeRangoFisicoError,
)
from domain.excepciones_cuentas import (
    CredencialesInvalidas, DatosInvalidos, PlantaNoEncontrada, SinLecturas,
    UsuarioYaExiste,
)


class SolicitudInvalida(Exception):
    """Error de forma de la petición (campo faltante, tipo incorrecto)."""


# Traducción excepción de dominio -> código HTTP. El dominio no conoce estos
# números: los pone el adaptador. La tabla completa está en docs/API.md.
_MAPA = [
    (SolicitudInvalida, 400),
    (LecturaInvalida, 400),
    (ValorFueraDeRangoFisicoError, 400),
    (DatosInvalidos, 400),
    (CredencialesInvalidas, 401),
    (AccesoDenegado, 403),
    (DispositivoInactivo, 403),
    (EspecieNoEncontradaError, 404),
    (PlantaNoEncontrada, 404),
    (SinLecturas, 404),
    (DispositivoNoEncontrado, 404),
    (UsuarioYaExiste, 409),
    (DispositivoYaVinculado, 409),
]


def registrar_manejadores(app: Flask) -> None:
    for excepcion, codigo in _MAPA:
        def _handler(error, codigo=codigo):
            return jsonify({"error": str(error)}), codigo
        app.register_error_handler(excepcion, _handler)

    @app.errorhandler(HTTPException)
    def _http(error):
        # 404 de ruta inexistente, 405 de método equivocado. Sin esto, el
        # manejador de Exception los convertiría en 500.
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def _inesperado(error):
        app.logger.exception("Error no controlado")
        return jsonify({"error": "Error interno"}), 500
