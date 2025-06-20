import unittest
import time
from models.plc_simulator import PLCSimulator


class TestPLCSimulator(unittest.TestCase):
    def setUp(self):
        self.plc_simulator = PLCSimulator('127.0.0.1', 2000)

    def test_connect(self):
        self.assertTrue(self.plc_simulator.connect())

    def test_send_command(self):
        self.plc_simulator.connect()
        result = self.plc_simulator.send_command(0)
        self.assertIn('status_code', result)
        self.assertIn('position', result)

    def test_send_command_muevete(self):
        self.plc_simulator.connect()
        initial_position = self.plc_simulator.current_position
        # Elegir una nueva posición distinta a la inicial
        new_position = initial_position + \
            1 if initial_position < 10 else initial_position - 1
        result = self.plc_simulator.send_command(1, new_position)
        time.sleep(2.5)
        self.assertEqual(self.plc_simulator.current_position, new_position)
        self.assertNotEqual(
            self.plc_simulator.current_position, initial_position)

    def test_send_command_error_en_movimiento(self):
        self.plc_simulator.connect()
        self.plc_simulator.is_running = True  # Forzar estado en movimiento
        result = self.plc_simulator.send_command(1, 2)
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'PLC en movimiento')

    def test_send_command_argumento_invalido(self):
        self.plc_simulator.connect()
        with self.assertRaises(Exception):
            self.plc_simulator.send_command(1, 999)  # Argumento fuera de rango

    def tearDown(self):
        self.plc_simulator.close()
