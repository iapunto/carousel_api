import unittest
from api import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_get_status(self):
        response = self.app.get('/v1/status')
        self.assertEqual(response.status_code, 200)
        self.assertIn('status_code', response.json)
        self.assertIn('position', response.json)

    def test_send_command_valid(self):
        data = {'command': 1, 'argument': 5}  # Comando MUEVETE con argumento válido
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'message': 'Comando enviado exitosamente'})

    def test_send_command_invalid_command(self):
        data = {'command': 'invalid', 'argument': 5}
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Comando inválido'})

    def test_send_command_invalid_argument(self):
        data = {'command': 1, 'argument': 15}  # Argumento fuera de rango
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Argumento inválido'})

    def test_send_command_missing_command(self):
        data = {'argument': 5}
        response = self.app.post('/v1/command', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {'error': 'Comando no especificado'})