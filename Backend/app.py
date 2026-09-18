import os
from flask import Flask, jsonify, request
import dataclasses

from application.use_cases import EvaluarMateraUseCase
from application.dto import EvaluacionRequestDTO
from infrastructure.csv_especie_repository import CsvEspecieRepository
from domain.exceptions import EspecieNoEncontradaError, ValorFueraDeRangoFisicoError

# 1. Inicializar la app de Flask
app = Flask(__name__)

# 2. Inyección de dependencias
ruta_csv = os.path.join(os.path.dirname(__file__), 'infrastructure', 'especies.csv')
repositorio = CsvEspecieRepository(ruta_csv)
caso_de_uso = EvaluarMateraUseCase(repositorio)

# 3. Endpoint de Health Check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"estado": "OK", "mensaje": "API de Matera Inteligente funcionando"}), 200

# 4. Endpoint Principal
@app.route('/api/v1/evaluar', methods=['POST'])
def evaluar_matera():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No se proporcionaron datos JSON"}), 400

    try:
        # Construir el DTO de Request extrayendo y convirtiendo los datos
        request_dto = EvaluacionRequestDTO(
            especie=data.get('especie'),
            humedad=float(data.get('humedad', 0.0)),
            luz=float(data.get('luz', 0.0)),
            temperatura=float(data.get('temperatura', 0.0))
        )
        
        # Ejecutar el caso de uso
        respuesta_dto = caso_de_uso.ejecutar(request_dto)
        
        # Convertir la respuesta a diccionario y enviarla
        respuesta_dict = dataclasses.asdict(respuesta_dto)
        return jsonify(respuesta_dict), 200

    except EspecieNoEncontradaError as e:
        return jsonify({"error": str(e)}), 404
    except ValorFueraDeRangoFisicoError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        # Por si falla el float() al convertir un string inválido
        return jsonify({"error": "Valores numéricos inválidos proporcionados."}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# 5. Arranque del servidor (siempre al final del archivo)
if __name__ == '__main__':
    app.run(debug=True, port=5000)
