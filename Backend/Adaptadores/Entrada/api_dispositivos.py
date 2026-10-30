from datetime import datetime, timezone

from flask import Blueprint, jsonify

from adaptadores.entrada.errores import SolicitudInvalida
from adaptadores.entrada.peticiones import cuerpo_json, numero, texto
from adaptadores.entrada.seguridad import dispositivo_requerido
from domain.comandos import RegistrarLecturaCmd


def _marca_tiempo(data) -> datetime:
    """Traduce el texto ISO 8601 a datetime con zona horaria (UTC si no trae)."""
    bruto = texto(data, "marca_tiempo")
    try:
        # En Python 3.9 fromisoformat no acepta el sufijo 'Z'
        marca = datetime.fromisoformat(bruto.replace("Z", "+00:00"))
    except ValueError:
        raise SolicitudInvalida("'marca_tiempo' no tiene formato ISO 8601")
    if marca.tzinfo is None:
        marca = marca.replace(tzinfo=timezone.utc)
    return marca.astimezone(timezone.utc)


def crear_blueprint_dispositivos(registrar_lectura) -> Blueprint:
    """registrar_lectura: RegistrarLecturaPort."""
    bp = Blueprint("api_dispositivos", __name__)

    @bp.post("/api/dispositivos/<id>/lecturas")
    @dispositivo_requerido
    def lecturas(id: str, dispositivo_id: str, planta_id: str):
        # El dispositivo solo puede reportar a nombre de sí mismo
        if id != dispositivo_id:
            return jsonify({"error": "El token no corresponde a este dispositivo"}), 403

        data = cuerpo_json()
        cmd = RegistrarLecturaCmd(
            dispositivo_id=dispositivo_id,        # viene del token verificado, no del cuerpo
            marca_tiempo=_marca_tiempo(data),
            humedad=numero(data, "humedad"),
            luz=numero(data, "luz"),
            temperatura=numero(data, "temperatura"),
        )
        # LecturaInvalida (humedad 140, etc.) y DispositivoInactivo los traduce errores.py
        estado = registrar_lectura.registrar(cmd)
        return jsonify({
            "planta_id": estado.planta_id,
            "vitalidad": estado.vitalidad,
        }), 201

    return bp