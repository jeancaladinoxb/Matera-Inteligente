"""Punto UNICO de composicion.

Es el unico archivo del backend que conoce clases concretas. El dominio recibe
sus puertos ya construidos y nunca instancia un adaptador.

Cambiar la tabla de referencia de CSV a base de datos es cambiar la variable
MATERA_TABLA y reiniciar: ni un archivo de domain/ se toca (R4).
"""

import os

from flask import Flask, jsonify
from flask_cors import CORS

from adaptadores.entrada.api_auth import crear_blueprint_auth
from adaptadores.entrada.api_dispositivos import crear_blueprint_dispositivos
from adaptadores.entrada.api_front import crear_blueprint_front
from adaptadores.entrada.errores import registrar_manejadores
from adaptadores.salida.bd import inicializar_bd
from adaptadores.salida.dispositivo_bd import DispositivoRepositorioBd
from adaptadores.salida.emisor_jwt import EmisorJwt
from adaptadores.salida.hasher_password import HasherPassword
from adaptadores.salida.historial_bd import HistorialLecturasBd
from adaptadores.salida.planta_bd import PlantaRepositorioBd
from adaptadores.salida.tabla_bd import TablaReferenciaBd
from adaptadores.salida.tabla_csv import TablaReferenciaCsv
from adaptadores.salida.usuario_bd import UsuarioRepositorioBd
from config import Config, cargar_config
from domain.servicios import (
    ConsultarEstadoServicio,
    ConsultarHistorialServicio,
    EvaluarLecturaServicio,
    ListarEspeciesServicio,
    ListarPlantasServicio,
    RegistrarLecturaServicio,
)
from domain.servicios_cuentas import AutenticarUsuarioServicio, VincularDispositivoServicio


def create_app(cfg: Config = None) -> Flask:
    cfg = cargar_config() if cfg is None else cfg

    # Las tablas se crean si no existen; es idempotente.
    inicializar_bd(cfg.ruta_db)

    # ---- Adaptadores de salida -------------------------------------------
    # R4: la unica linea del sistema que decide de donde salen los rangos.
    # Las dos implementan TablaReferenciaPort, asi que el dominio no se entera.
    tabla = TablaReferenciaBd(cfg.ruta_db) if cfg.tabla == "bd" else TablaReferenciaCsv(cfg.ruta_csv)

    historial = HistorialLecturasBd(cfg.ruta_db)
    plantas = PlantaRepositorioBd(cfg.ruta_db)
    dispositivos = DispositivoRepositorioBd(cfg.ruta_db)
    usuarios = UsuarioRepositorioBd(cfg.ruta_db)
    emisor = EmisorJwt(cfg.jwt_secret)
    hasher = HasherPassword()

    # ---- Casos de uso (implementan los puertos de entrada) ----------------
    evaluar_lectura = EvaluarLecturaServicio(tabla)
    listar_especies = ListarEspeciesServicio(tabla)
    registrar_lectura = RegistrarLecturaServicio(tabla, historial, plantas, dispositivos)
    consultar_estado = ConsultarEstadoServicio(plantas, historial)
    consultar_historial = ConsultarHistorialServicio(plantas, historial)
    listar_plantas = ListarPlantasServicio(plantas)
    vincular_dispositivo = VincularDispositivoServicio(plantas, dispositivos, tabla, emisor)
    autenticar = AutenticarUsuarioServicio(usuarios, hasher, emisor)

    # ---- Adaptadores de entrada -------------------------------------------
    app = Flask(__name__)
    CORS(
        app,
        origins=cfg.cors_origins or ["http://localhost:5500"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.register_blueprint(crear_blueprint_auth(autenticar))
    app.register_blueprint(
        crear_blueprint_front(
            consultar_estado,
            consultar_historial,
            listar_plantas,
            vincular_dispositivo,
            evaluar_lectura,
            listar_especies,
        )
    )
    # El adaptador del ESP32: entro sin tocar domain/ (prueba de cambio).
    app.register_blueprint(crear_blueprint_dispositivos(registrar_lectura))

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"estado": "OK", "tabla": cfg.tabla}), 200

    # Siempre despues de registrar los blueprints.
    registrar_manejadores(app)
    return app


if __name__ == "__main__":
    create_app().run(
        debug=os.environ.get("MATERA_DEBUG", "1") == "1",
        port=int(os.environ.get("MATERA_PORT", "5000")),
    )
