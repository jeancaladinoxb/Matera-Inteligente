from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities import RangoEspecie

# Principio de Inversion de Dependencias (DIP): La capa de dominio define la abstraccion del repositorio.
# Las capas de nivel superior no dependen de detalles de infraestructura como archivos CSV o bases de datos,
# sino de contratos definidos en el dominio.

# Principio de Segregacion de Interfaces (ISP): La interfaz define unicamente los metodos indispensables
# para las necesidades de consulta del dominio de la matera inteligente.

# Principio de Sustitucion de Liskov (LSP): Cualquier clase que implemente EspecieRepository podra ser usada
# indistintamente sin alterar la correccion del programa.

class EspecieRepository(ABC):
    """
    Interfaz abstracta del repositorio de especies.
    """

    @abstractmethod
    def obtener_por_nombre(self, nombre_especie: str) -> Optional[RangoEspecie]:
        """
        Busca y retorna los rangos ideales para una especie dada por su nombre.
        Retorna None si la especie no se encuentra registrada.
        """
        pass

    @abstractmethod
    def listar_especies(self) -> List[str]:
        """
        Retorna la lista de nombres de especies disponibles en el repositorio.
        """
        pass
    @abstractmethod
    def obtener_todas_las_especies(self) -> List[RangoEspecie]:
        """
        Retorna la lista de todas las especies con sus respectivos rangos ideales.
        """
        pass
