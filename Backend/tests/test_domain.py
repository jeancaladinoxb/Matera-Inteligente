import unittest
from domain.entities import LecturaSensores, RangoEspecie
from domain.value_objects import EstadoParametro
from domain.services import EvaluadorVitalidadService
from domain.excepciones import ValorFueraDeRangoFisicoError, EspecieNoEncontradaError
from domain.repositories import EspecieRepository
from application.dto import EvaluacionRequestDTO
from application.use_cases import EvaluarMateraUseCase

# Principio de Responsabilidad Unica (SRP): Este archivo agrupa las pruebas unitarias
# exclusivas para validar las reglas de negocio del dominio y los casos de uso de aplicacion.

class MockEspecieRepository(EspecieRepository):
    """
    Doble de prueba (Mock/Fake) que simula el repositorio de especies en memoria.
    Principio de Inversion de Dependencias (DIP): Permite probar los casos de uso sin Flask ni CSV real.
    """
    def __init__(self):
        self.especies = {
            "Orquidea": RangoEspecie(
                nombre_especie="Orquidea",
                humedad_min=40.0, humedad_max=70.0,
                luz_min=10000.0, luz_max=20000.0,
                temp_min=18.0, temp_max=25.0
            )
        }

    def obtener_por_nombre(self, nombre: str):
        return self.especies.get(nombre)

    def listar_especies(self):
        return list(self.especies.keys())


class TestDominioMatera(unittest.TestCase):

    def setUp(self):
        self.evaluador = EvaluadorVitalidadService()
        self.rango_orquidea = RangoEspecie(
            nombre_especie="Orquidea",
            humedad_min=40.0, humedad_max=70.0,
            luz_min=10000.0, luz_max=20000.0,
            temp_min=18.0, temp_max=25.0
        )

    def test_01_lectura_valida_evaluacion_optima(self):
        """
        Prueba 1: Verifica que lecturas dentro de los rangos optimos generen estados OPTIMO y 100% de vitalidad.
        """
        lecturas = LecturaSensores(humedad=50.0, luz=15000.0, temperatura=20.0)
        resultado = self.evaluador.evaluar(lecturas, self.rango_orquidea)

        self.assertEqual(resultado.estado_humedad, EstadoParametro.OPTIMO)
        self.assertEqual(resultado.estado_luz, EstadoParametro.OPTIMO)
        self.assertEqual(resultado.estado_temperatura, EstadoParametro.OPTIMO)
        self.assertEqual(resultado.indice_vitalidad.porcentaje, 100.0)
        self.assertEqual(resultado.indice_vitalidad.nivel, "EXCELENTE")

    def test_02_lectura_humedad_alta_y_temperatura_baja(self):
        """
        Prueba 2: Verifica la correcta clasificacion de ALTO y BAJO en los parametros de la matera.
        """
        lecturas = LecturaSensores(humedad=80.0, luz=15000.0, temperatura=10.0)
        resultado = self.evaluador.evaluar(lecturas, self.rango_orquidea)

        self.assertEqual(resultado.estado_humedad, EstadoParametro.ALTO)
        self.assertEqual(resultado.estado_luz, EstadoParametro.OPTIMO)
        self.assertEqual(resultado.estado_temperatura, EstadoParametro.BAJO)
        self.assertLess(resultado.indice_vitalidad.porcentaje, 100.0)

    def test_03_validacion_valores_fisicamente_imposibles_lanza_excepcion(self):
        """
        Prueba 3 (RF6): Verifica que ingresar humedad negativa (-5%) lance la excepcion ValorFueraDeRangoFisicoError.
        """
        with self.assertRaises(ValorFueraDeRangoFisicoError) as cm:
            LecturaSensores(humedad=-5.0, luz=10000.0, temperatura=20.0)
        
        self.assertEqual(cm.exception.campo, "humedad")
        self.assertEqual(cm.exception.valor, -5.0)

    def test_04_validacion_temperatura_imposible_lanza_excepcion(self):
        """
        Prueba 4 (RF6): Verifica que una temperatura de 100°C lance ValorFueraDeRangoFisicoError.
        """
        with self.assertRaises(ValorFueraDeRangoFisicoError) as cm:
            LecturaSensores(humedad=50.0, luz=10000.0, temperatura=100.0)

        self.assertEqual(cm.exception.campo, "temperatura")

    def test_05_caso_de_uso_especie_desconocida_lanza_excepcion(self):
        """
        Prueba 5: Verifica que solicitar una especie no registrada lance EspecieNoEncontradaError.
        """
        repo_mock = MockEspecieRepository()
        use_case = EvaluarMateraUseCase(repo_mock)
        request = EvaluacionRequestDTO(especie="RosaDesconocida", humedad=50.0, luz=15000.0, temperatura=20.0)

        with self.assertRaises(EspecieNoEncontradaError) as cm:
            use_case.ejecutar(request)

        self.assertEqual(cm.exception.nombre_especie, "RosaDesconocida")

    def test_06_caso_de_uso_ejecucion_exitosa_con_doble_de_prueba(self):
        """
        Prueba 6: Verifica el flujo completo del caso de uso de evaluacion usando el doble de prueba del repositorio.
        """
        repo_mock = MockEspecieRepository()
        use_case = EvaluarMateraUseCase(repo_mock)
        request = EvaluacionRequestDTO(especie="Orquidea", humedad=50.0, luz=15000.0, temperatura=20.0)

        response = use_case.ejecutar(request)

        self.assertTrue(response.exito)
        self.assertEqual(response.especie, "Orquidea")
        self.assertEqual(response.porcentaje_vitalidad, 100.0)

    def test_07_listar_especies_devuelve_lista_serializable(self):
        """
        Prueba 7: Confirma que la funcion del caso de uso para listar especies retorna una estructura directamente serializable por Flask (List[str]).
        """
        repo_mock = MockEspecieRepository()
        use_case = EvaluarMateraUseCase(repo_mock)

        especies = use_case.obtener_especies_disponibles()

        self.assertIsInstance(especies, list)
        self.assertEqual(especies, ["Orquidea"])
        # Verificar que todos los elementos sean strings (directamente JSON serializable)
        self.assertTrue(all(isinstance(e, str) for e in especies))


if __name__ == "__main__":
    unittest.main()
