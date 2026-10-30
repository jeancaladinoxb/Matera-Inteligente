# PROVISIONAL (Julián, commit 0): prueba de contrato de los puertos de salida y de entrada.
import inspect
import unittest

from domain.puertos import entrada, salida

CONTRATO_SALIDA = {
    "TablaReferenciaPort": {"por_especie": ["nombre"], "todas": []},
    "HistorialLecturasPort": {
        "guardar": ["planta_id", "lectura", "evaluacion"],
        "ultima": ["planta_id"],
        "historial": ["planta_id", "limite"],
    },
    "PlantaRepositorioPort": {"guardar": ["planta"], "por_id": ["planta_id"], "de_usuario": ["usuario_id"]},
    "DispositivoRepositorioPort": {
        "guardar": ["dispositivo"], "por_id": ["dispositivo_id"], "por_codigo": ["codigo"],
    },
    "UsuarioRepositorioPort": {
        "guardar": ["usuario"], "por_email": ["email"], "por_id": ["usuario_id"],
    },
    "EmisorTokenPort": {
        "token_usuario": ["usuario_id"], "token_dispositivo": ["dispositivo_id", "planta_id"],
    },
    "HasherPasswordPort": {"hashear": ["password"], "coincide": ["password", "password_hash"]},
}

# Nombres de método tomados del código de Jeancarlo (adaptadores/entrada).
CONTRATO_ENTRADA = {
    "RegistrarLecturaPort": {"registrar": ["cmd"]},
    "EvaluarLecturaPort": {"evaluar": ["especie", "humedad", "luz", "temperatura"]},
    "ConsultarEstadoPort": {"consultar": ["usuario_id", "planta_id"]},
    "ConsultarHistorialPort": {"historial": ["usuario_id", "planta_id", "limite"]},
    "ListarPlantasPort": {"listar": ["usuario_id"]},
    "ListarEspeciesPort": {"listar": []},
    "VincularDispositivoPort": {"vincular": ["usuario_id", "nombre", "especie", "codigo"]},
    "AutenticarUsuarioPort": {
        "registrar": ["email", "password"], "iniciar_sesion": ["email", "password"],
    },
}


def _metodos(puerto):
    """Método público -> lista de nombres de parámetros (sin self)."""
    return {
        nombre: list(inspect.signature(f).parameters)[1:]
        for nombre, f in vars(puerto).items()
        if not nombre.startswith("_") and inspect.isfunction(f)
    }


class TestContratoPuertos(unittest.TestCase):
    def _comprobar(self, modulo, contrato):
        for nombre_puerto, esperado in contrato.items():
            with self.subTest(puerto=nombre_puerto):
                puerto = getattr(modulo, nombre_puerto, None)
                self.assertIsNotNone(puerto, "Falta el puerto %s en %s" % (nombre_puerto, modulo.__name__))
                reales = _metodos(puerto)
                self.assertEqual(
                    sorted(reales), sorted(esperado),
                    "%s: métodos distintos al contrato (reales=%s, esperados=%s)"
                    % (nombre_puerto, sorted(reales), sorted(esperado)),
                )
                for metodo, params in esperado.items():
                    self.assertEqual(
                        reales[metodo], params,
                        "%s.%s: parámetros distintos al contrato" % (nombre_puerto, metodo),
                    )

    def test_puertos_de_salida(self):
        self._comprobar(salida, CONTRATO_SALIDA)

    def test_puertos_de_entrada(self):
        self._comprobar(entrada, CONTRATO_ENTRADA)


if __name__ == "__main__":
    unittest.main()
