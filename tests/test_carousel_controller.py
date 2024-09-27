import unittest
from unittest.mock import MagicMock
from controllers.carousel_controller import CarouselController
from models.plc_simulator import PLCSimulator

class TestCarouselController(unittest.TestCase):
    def setUp(self):
        self.plc_simulator = PLCSimulator('127.0.0.1', 2000)
        self.controller = CarouselController(self.plc_simulator)

    def test_send_command_muevete_valid(self):
        # Simula que el PLC está listo para moverse
        self.plc_simulator.is_running = False
        self.plc_simulator.status_code = 0b00100001  # Estado "listo"

        # Envía el comando MUEVETE con un argumento válido
        self.controller.send_command(1, 5)

        # Verifica que el carrusel se movió a la posición correcta
        self.assertEqual(self.plc_simulator.current_position, 5)

    def test_send_command_muevete_invalid_argument(self):
        # Envía el comando MUEVETE con un argumento inválido
        self.controller.send_command(1, 15)  # Fuera de rango

        # Verifica que se imprime el mensaje de error
        # Puedes usar assertLogs o capturar la salida estándar para verificar esto

    def test_send_command_muevete_plc_not_ready(self):
        # Simula que el PLC no está listo para moverse
        self.plc_simulator.is_running = True
        self.plc_simulator.status_code = 0b00100010  # Estado "en movimiento"

        # Envía el comando MUEVETE
        self.controller.send_command(1, 3)

        # Verifica que se imprime el mensaje de error
        # Puedes usar assertLogs o capturar la salida estándar para verificar esto

    # Agrega más pruebas para otros comandos y escenarios

    def tearDown(self):
        self.plc_simulator.close()