from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from adaptadores.entrada.errores import SolicitudInvalida
from adaptadores.entrada.seguridad import usuario_requerido


# ---------- Utilidades de traducción (solo forma, nunca reglas de negocio) ----------

def _cuerpo_json() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise SolicitudInvalida("El cuerpo debe ser un objeto JSON")
    return data


def _texto(data: Dict[str, Any], campo: str) -> str:
    valor = data.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise SolicitudInvalida("Falta el campo '%s' o no es texto" % campo)
    return valor.strip()


def _numero(data: Dict[str, Any], campo: str) -> float:
    valor = data.get(campo)
    # bool es subclase de int en Python, se excluye explícitamente
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise SolicitudInvalida("Falta el campo '%s' o no es numérico" % campo)
    return float(valor)


def _limite(valor: Optional[str], por_defecto: int = 20, maximo: int = 200) -> int:
    if valor is None:
        return por_defecto
    try:
        limite = int(valor)
    except ValueError:
        raise SolicitudInvalida("'limite' debe ser un entero")
    if limite <= 0 or limite > maximo:
        raise SolicitudInvalida("'limite' debe estar entre 1 y %d" % maximo)
    return limite


def _medicion(lectura, evaluacion) -> Dict[str, Any]:
    """Traduce una evaluacion del dominio al JSON de docs/API.md.

    Los enums salen con .value y el indice de vitalidad se abre en porcentaje
    y nivel: el dominio no sabe nada de JSON, la traduccion es aqui.
    """
    return {
        "lecturas": {
            "humedad": lectura.humedad,
            "luz": lectura.luz,
            "temperatura": lectura.temperatura,
        },
        "estados": {
            "humedad": evaluacion.estado_humedad.value,
            "luz": evaluacion.estado_luz.value,
            "temperatura": evaluacion.estado_temperatura.value,
        },
        "vitalidad": {
            "porcentaje": evaluacion.indice_vitalidad.porcentaje,
            "nivel": evaluacion.indice_vitalidad.nivel,
        },
    }


def _estado_a_dict(estado) -> Dict[str, Any]:
    """EstadoPlanta -> JSON. La especie y el dispositivo salen de la propia
    lectura evaluada; el nombre de la planta lo tiene el cliente de GET /api/plantas."""
    cuerpo = {
        "planta_id": estado.planta_id,
        "especie": estado.evaluacion.nombre_especie,
        "dispositivo_id": estado.lectura.dispositivo_id,
        "marca_tiempo": estado.lectura.marca_tiempo.isoformat(),
    }
    cuerpo.update(_medicion(estado.lectura, estado.evaluacion))
    return cuerpo


# ---------- Blueprint ----------

def crear_blueprint_front(
    consultar_estado,      # ConsultarEstadoPort
    consultar_historial,   # ConsultarHistorialPort (por definir con A)
    listar_plantas,        # ListarPlantasPort      (por definir con A)
    vincular_dispositivo,  # VincularDispositivoPort
    evaluar_lectura,       # EvaluarLecturaPort     (R1, por definir con A)
    listar_especies,       # ListarEspeciesPort     (por definir con A)
) -> Blueprint:
    bp = Blueprint("api_front", __name__)

    @bp.get("/api/especies")
    @usuario_requerido
    def especies(usuario_id: str):
        return jsonify([
            {
                "nombre": e.nombre,
                "rangos": {
                    "humedad": {"min": e.humedad_min, "max": e.humedad_max},
                    "luz": {"min": e.luz_min, "max": e.luz_max},
                    "temperatura": {"min": e.temp_min, "max": e.temp_max},
                },
            }
            for e in listar_especies.listar()
        ]), 200

    @bp.post("/api/evaluar")
    @usuario_requerido
    def evaluar(usuario_id: str):
        data = _cuerpo_json()
        resultado = evaluar_lectura.evaluar(
            especie=_texto(data, "especie"),
            humedad=_numero(data, "humedad"),
            luz=_numero(data, "luz"),
            temperatura=_numero(data, "temperatura"),
        )
        cuerpo = {"especie": resultado.nombre_especie}
        cuerpo.update(_medicion(resultado.lecturas, resultado))
        return jsonify(cuerpo), 200

    @bp.post("/api/plantas")
    @usuario_requerido
    def vincular(usuario_id: str):
        data = _cuerpo_json()
        vinculada = vincular_dispositivo.vincular(
            usuario_id,
            _texto(data, "nombre"),
            _texto(data, "especie"),
            _texto(data, "codigo"),
        )
        return jsonify({
            "planta_id": vinculada.planta_id,
            "dispositivo_id": vinculada.dispositivo_id,
            "token_dispositivo": vinculada.token_dispositivo,
        }), 201

    @bp.get("/api/plantas")
    @usuario_requerido
    def plantas(usuario_id: str):
        return jsonify([
            {"planta_id": p.planta_id, "nombre": p.nombre, "especie": p.especie}
            for p in listar_plantas.listar(usuario_id)
        ]), 200

    @bp.get("/api/plantas/<planta_id>/estado")
    @usuario_requerido
    def estado(usuario_id: str, planta_id: str):
        # AccesoDenegado y no encontrado los traduce el manejador central
        return jsonify(_estado_a_dict(consultar_estado.consultar(usuario_id, planta_id))), 200

    @bp.get("/api/plantas/<planta_id>/historial")
    @usuario_requerido
    def historial(usuario_id: str, planta_id: str):
        limite = _limite(request.args.get("limite"))
        items = consultar_historial.historial(usuario_id, planta_id, limite)
        return jsonify([_estado_a_dict(e) for e in items]), 200

    return bp