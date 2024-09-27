import unittest
from models.plc_simulator import PLCSimulator

class TestPLCSimulator(unittest.TestCase):
    def setUp(self):
        self.plc_simulator = PLCSimulator('127.0.0.1', 2000)

    def test_connect(self):
        """
        Prueba el método connect del simulador.
        """
        self.assertTrue(self.plc_simulator.connect())

    def test_send_command(self):
        """
        Prueba el método send_command del simulador.
        """
        self.plc_simulator.connect()
        self.plc_simulator.send_command(0)  # Envía el comando de estado
        # Puedes agregar más aserciones aquí para verificar el comportamiento del simulador

    def test_receive_status(self):
        """
        Prueba el método receive_status del simulador.
        """
        self.plc_simulator.connect()
        status_code = self.plc_simulator.receive_status()
        self.assertIsNotNone(status_code)
        self.assertIsInstance(status_code, int)
        self.assertTrue(0 <= status_code <= 255)

    def test_receive_position(self):
        """
        Prueba el método receive_position del simulador.
        """
        self.plc_simulator.connect()
        position = self.plc_simulator.receive_position()
        self.assertIsNotNone(position)
        self.assertIsInstance(position, int)
        self.assertTrue(0 <= position <= 9)

    def tearDown(self):
        self.plc_simulator.close()