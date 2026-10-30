# PROVISIONAL (Julián, commit 0): el dominio no puede importar infraestructura ni frameworks.
import ast
import unittest
from pathlib import Path

DOMINIO = Path(__file__).resolve().parents[2] / "domain"
PROHIBIDOS = {"flask", "jwt", "csv", "sqlite3", "json"}


def _importados(ruta: Path):
    """Módulos raíz importados por el archivo, leyendo el árbol sintáctico (no el texto)."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                yield alias.name.split(".")[0]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and nodo.module:
            yield nodo.module.split(".")[0]


class TestAislamientoDominio(unittest.TestCase):
    def test_dominio_no_importa_infraestructura(self):
        archivos = sorted(DOMINIO.rglob("*.py"))
        self.assertTrue(archivos, "No se encontraron archivos en %s" % DOMINIO)
        for ruta in archivos:
            with self.subTest(archivo=str(ruta.relative_to(DOMINIO.parent))):
                prohibidos = sorted(set(_importados(ruta)) & PROHIBIDOS)
                self.assertEqual(prohibidos, [], "importa módulos prohibidos: %s" % prohibidos)


if __name__ == "__main__":
    unittest.main()
