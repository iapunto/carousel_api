import unittest
from carousel_api.api import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.config['MODE'] = 'simulator'  # Asegúrate de usar el simulador en las pruebas

    def test_get_status(self):
        """
        Prueba el endpoint /v1/status (GET).
        """
        response = self.app.get('/v1/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status_code', data)
        self.assertIn('position', data)

    def test_send_command_muevete_valid(self):
        """
        Prueba el endpoint /v1/command (POST) con el comando MUEVETE y un argumento válido.
        """
        data = {'command': 1, 'argument': 5}
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'message': 'Comando enviado exitosamente'})

    def test_send_command_muevete_invalid_argument(self):
        """
        Prueba el endpoint /v1/command (POST) con el comando MUEVETE y un argumento inválido.
        """
        data = {'command': 1, 'argument': 15}  # Argumento fuera de rango
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Argumento inválido'})

    def test_send_command_missing_command(self):
        """
        Prueba el endpoint /v1/command (POST) sin especificar el comando.
        """
        data = {'argument': 5}
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Comando no especificado'})

    # Agrega más pruebas para otros comandos y escenarios según sea necesario