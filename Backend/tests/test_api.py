import unittest
import json
from app import app 

class TestAPIMatera(unittest.TestCase):

    def setUp(self):
       
        self.cliente = app.test_client()
        self.cliente.testing = True

    def test_01_borde_humedad_negativa_retorna_400(self):
       
        payload_invalido = {
            "especie": "Orquidea",
            "humedad": -10.0,
            "luz": 15000.0,
            "temperatura": 22.0
        }

        # Simulamos un POST al endpoint
        respuesta = self.cliente.post(
            '/api/v1/evaluar',
            data=json.dumps(payload_invalido),
            content_type='application/json'
        )

       
        self.assertEqual(respuesta.status_code, 400)
        
       
        datos_respuesta = json.loads(respuesta.data)
        self.assertIn("error", datos_respuesta)
        self.assertIn("humedad", datos_respuesta["error"])

    def test_02_borde_especie_inexistente_retorna_404(self):
        
        payload_inexistente= {
            "especie" : "Bonzai",
            "humedad": 50.0,
            "luz": 15000.0,
            "temperatura": 22.0
        }

        respuesta = self.cliente.post(
            '/api/v1/evaluar',
            data = json.dumps(payload_inexistente),
            content_type ='application/json'
        )
        self.assertEqual(respuesta.status_code, 404)
    


if __name__ == "__main__":
    unittest.main()
