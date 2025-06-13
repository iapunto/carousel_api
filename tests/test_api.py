import unittest
import json
from api import create_app
from models.plc_simulator import PLCSimulator


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.plc = PLCSimulator('127.0.0.1', 2000)
        self.app = create_app(self.plc)
        self.client = self.app.test_client()

    def test_status_ok(self):
        response = self.client.get('/v1/status')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('status_code', data)
        self.assertIn('position', data)

    def test_command_ok(self):
        payload = {'command': 1, 'argument': 3}
        response = self.client.post('/v1/command', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.get_json())

    def test_command_invalid_json(self):
        response = self.client.post(
            '/v1/command', data='nojson', content_type='text/plain')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_command_missing_command(self):
        response = self.client.post('/v1/command', json={'argument': 2})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_command_out_of_range(self):
        response = self.client.post(
            '/v1/command', json={'command': 999, 'argument': 2})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())

    def test_command_argument_out_of_range(self):
        response = self.client.post(
            '/v1/command', json={'command': 1, 'argument': 999})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())


if __name__ == '__main__':
    unittest.main()
