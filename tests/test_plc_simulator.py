import unittest
from models.plc_simulator import PLCSimulator

class TestPLCSimulator(unittest.TestCase):
    def setUp(self):
        self.plc_simulator = PLCSimulator('127.0.0.1', 2000)  # No se usan realmente la IP y el puerto en el simulador

    def test_connect(self):
        self.assertTrue(self.plc_simulator.connect())

    def test_send_command(self):
        self.plc_simulator.connect()
        self.plc_simulator.send_command(0)  # Envía el comando de estado
        # Puedes agregar más aserciones aquí para verificar el comportamiento del simulador

    def test_receive_response(self):
        self.plc_simulator.connect()
        self.plc_simulator.send_command(0)  # Envía el comando de estado
        response = self.plc_simulator.receive_response()
        self.assertIsNotNone(response)
        self.assertIn('status_code', response)
        self.assertIn('position', response)

    def tearDown(self):
        self.plc_simulator.close()