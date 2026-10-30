import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import dataclasses

from application.use_cases import EvaluarMateraUseCase
from application.dto import EvaluacionRequestDTO
from infrastructure.csv_especie_repository import CsvEspecieRepository
from domain.excepciones import EspecieNoEncontradaError, ValorFueraDeRangoFisicoError

# NUEVO: adaptadores de la fase 2
from adaptadores.entrada.api_dispositivos import crear_blueprint_dispositivos
from adaptadores.entrada.errores import registrar_manejadores
from fakes_temporales import FakeRegistrarLectura   # NUEVO: borrar cuando llegue el dominio real

# 1. Inicializar la app de Flask
app = Flask(__name__)
CORS(app)

# 2. Inyección de dependencias
ruta_csv = os.path.join(os.path.dirname(__file__), 'infrastructure', 'especies.csv')
repositorio = CsvEspecieRepository(ruta_csv)
caso_de_uso = EvaluarMateraUseCase(repositorio)

# NUEVO: puerto falso mientras A termina RegistrarLecturaPort
registrar_lectura = FakeRegistrarLectura()

# NUEVO: registro del adaptador de dispositivos (línea de la prueba de cambio)
app.register_blueprint(crear_blueprint_dispositivos(registrar_lectura=registrar_lectura))
registrar_manejadores(app)   # siempre después de registrar los blueprints

# 3. Endpoint de Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"estado": "OK", "mensaje": "API de Matera Inteligente funcionando"}), 200

# Endpoint para exponer el catálogo de especies (Requisito RF5)
@app.route('/api/v1/especies', methods=['GET'])
def listar_especies_rf5():
    try:
        catalogo = caso_de_uso.obtener_catalogo_especies()
        return jsonify(catalogo), 200
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route('/api/v1/evaluar', methods=['POST'])
def evaluar_matera():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se proporcionaron datos JSON"}), 400

    try:
        request_dto = EvaluacionRequestDTO(
            especie=data.get('especie'),
            humedad=float(data.get('humedad', 0.0)),
            luz=float(data.get('luz', 0.0)),
            temperatura=float(data.get('temperatura', 0.0))
        )

        respuesta_dto = caso_de_uso.ejecutar(request_dto)

        respuesta_dict = dataclasses.asdict(respuesta_dto)
        return jsonify(respuesta_dict), 200

    except EspecieNoEncontradaError as e:
        return jsonify({"error": str(e)}), 404
    except ValorFueraDeRangoFisicoError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": "Valores numéricos inválidos proporcionados."}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# 5. Arranque del servidor (siempre al final del archivo)
if __name__ == '__main__':
    app.run(debug=True, port=5000)