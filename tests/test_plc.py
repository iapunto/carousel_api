import unittest
from models.plc import PLC

class TestPLC(unittest.TestCase):
    def setUp(self):
        self.plc = PLC('127.0.0.1', 2000)  # Reemplaza con la IP y puerto reales del PLC

    def test_connect(self):
        self.assertTrue(self.plc.connect())

    def test_send_command(self):
        self.plc.connect()
        self.plc.send_command(0)  # Envía el comando de estado
        # Puedes agregar más aserciones aquí para verificar la respuesta del PLC si es necesario

    def test_receive_response(self):
        self.plc.connect()
        self.plc.send_command(0)  # Envía el comando de estado
        response = self.plc.receive_response()
        self.assertIsNotNone(response)
        self.assertIn('status_code', response)
        self.assertIn('position', response)

    def tearDown(self):
        self.plc.close()