from typing import List, Dict
from domain.repositories import EspecieRepository
from domain.entities import LecturaSensores
from domain.services import EvaluadorVitalidadService
from domain.excepciones import EspecieNoEncontradaError
from application.dto import EvaluacionRequestDTO, EvaluacionResponseDTO

# Principio de Inversion de Dependencias (DIP): El caso de uso no depende de una implementacion concreta
# de infraestructura, sino de la interfaz abstracta EspecieRepository.

# Principio de Responsabilidad Unica (SRP): La clase EvaluarMateraUseCase tiene como unica responsabilidad
# orquestar el flujo de evaluacion consultando el repositorio y delegando la logica al servicio de dominio.

class EvaluarMateraUseCase:
    """
    Caso de uso principal para la evaluacion del estado ambiental e indice de vitalidad de una matera.
    """

    def __init__(self, especie_repository: EspecieRepository):
        # Inyeccion de Dependencias a traves de la abstraccion del repositorio (DIP)
        self.especie_repository = especie_repository
        self.evaluador_service = EvaluadorVitalidadService()

    def ejecutar(self, request: EvaluacionRequestDTO) -> EvaluacionResponseDTO:
        """
        Ejecuta el analisis de la matera para la especie y lecturas proporcionadas.
        Lanza EspecieNoEncontradaError si la especie no existe en el repositorio (mapeable a 404 por Persona 2).
        Lanza ValorFueraDeRangoFisicoError si las lecturas superan los limites fisicos (mapeable a 400 por Persona 2).
        """
        # 1. Validar y consultar el rango de la especie en el repositorio (DIP)
        rango_especie = self.especie_repository.obtener_por_nombre(request.especie)

        if not rango_especie:
            raise EspecieNoEncontradaError(request.especie)

        # 2. Crear entidad con las lecturas de los sensores (Valida limites fisicos)
        lecturas = LecturaSensores(
            humedad=request.humedad,
            luz=request.luz,
            temperatura=request.temperatura
        )

        # 3. Delegar el calculo de vitalidad al servicio de dominio (SRP)
        resultado = self.evaluador_service.evaluar(lecturas, rango_especie)

        # 4. Construir y retornar el DTO de respuesta
        return EvaluacionResponseDTO(
            exito=True,
            mensaje="Evaluacion realizada con exito.",
            especie=resultado.nombre_especie,
            humedad_medida=resultado.lecturas.humedad,
            luz_medida=resultado.lecturas.luz,
            temperatura_medida=resultado.lecturas.temperatura,
            estado_humedad=resultado.estado_humedad.value,
            estado_luz=resultado.estado_luz.value,
            estado_temperatura=resultado.estado_temperatura.value,
            porcentaje_vitalidad=resultado.indice_vitalidad.porcentaje,
            nivel_vitalidad=resultado.indice_vitalidad.nivel
        )

    def obtener_especies_disponibles(self) -> List[str]:
        """
        Retorna la lista de nombres de especies registradas en el repositorio.
        Estructura directamente serializable a JSON por Persona 2 (List[str]).
        """
        return self.especie_repository.listar_especies()

    def obtener_especies_para_presentacion(self) -> List[Dict[str, str]]:
        """
        Retorna la lista de especies formateadas como diccionarios {'nombre': 'Orquidea'}.
        Ideal para que Persona 2 construya selectores u opciones en el Frontend HTML/JS.
        """
        nombres = self.especie_repository.listar_especies()
        return [{"nombre": nombre} for nombre in nombres]
    def obtener_catalogo_especies(self) -> List[Dict]:
        """
        Retorna todas las especies con sus rangos formateadas para RF5.
        """
        especies = self.especie_repository.obtener_todas_las_especies()
        catalogo = []
        for e in especies:
            catalogo.append({
                "nombre": e.nombre_especie,
                "rangos": {
                    "humedad": {"min": e.humedad_min, "max": e.humedad_max},
                    "luz": {"min": e.luz_min, "max": e.luz_max},
                    "temperatura": {"min": e.temp_min, "max": e.temp_max}
                }
            })
        return catalogo
