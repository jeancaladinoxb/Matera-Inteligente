import csv
import os
from typing import Optional, List, Dict
from domain.entities import RangoEspecie
from domain.repositories import EspecieRepository

# Principio de Inversion de Dependencias (DIP): La capa de infraestructura depende de las abstracciones
# definidas en el dominio. CsvEspecieRepository implementa el contrato EspecieRepository.

# Principio de Sustitucion de Liskov (LSP): Esta implementacion concreta puede sustituir a cualquier
# otra implementacion de EspecieRepository sin romper el funcionamiento de los casos de uso.

# Principio de Responsabilidad Unica (SRP): Esta clase tiene la responsabilidad unica de leer y parsear
# los datos del archivo CSV para convertirlos en entidades del dominio (RangoEspecie).

class CsvEspecieRepository(EspecieRepository):
    """
    Implementacion concreta del repositorio de especies basada en la lectura de un archivo CSV.
    """

    def __init__(self, ruta_csv: Optional[str] = None):
        if ruta_csv is None:
            # Ruta por defecto relativa a la ubicacion del archivo actual
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_csv = os.path.join(directorio_actual, "especies.csv")
        self.ruta_csv = ruta_csv

    def _cargar_todas(self) -> Dict[str, RangoEspecie]:
        """
        Metodo privado para cargar y parsear el archivo CSV.
        Retorna un diccionario mapeando el nombre en minusculas con su entidad RangoEspecie.
        """
        especies: Dict[str, RangoEspecie] = {}

        if not os.path.exists(self.ruta_csv):
            raise FileNotFoundError(f"No se encontro el archivo de especies en: {self.ruta_csv}")

        with open(self.ruta_csv, mode="r", encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                nombre = fila["especie"].strip()
                rango = RangoEspecie(
                    nombre_especie=nombre,
                    humedad_min=float(fila["humedad_min"]),
                    humedad_max=float(fila["humedad_max"]),
                    luz_min=float(fila["luz_min"]),
                    luz_max=float(fila["luz_max"]),
                    temp_min=float(fila["temp_min"]),
                    temp_max=float(fila["temp_max"])
                )
                especies[nombre.lower()] = rango

        return especies

    def obtener_por_nombre(self, nombre_especie: str) -> Optional[RangoEspecie]:
        """
        Busca una especie por su nombre (insensible a mayusculas/minusculas).
        """
        if not nombre_especie:
            return None
        especies = self._cargar_todas()
        return especies.get(nombre_especie.strip().lower())

    def listar_especies(self) -> List[str]:
        """
        Retorna la lista con los nombres de las especies registradas en el CSV.
        """
        especies = self._cargar_todas()
        return [rango.nombre_especie for rango in especies.values()]
