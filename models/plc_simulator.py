"""
Simulador de PLC para desarrollo y pruebas.

Emula el comportamiento de un PLC Delta AS Series para pruebas de la API y la interfaz gráfica, sin necesidad de hardware real.

Autor: IA Punto: Soluciones Integrales de Tecnología y Marketing
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha: 2024-09-27
"""

import random
import time
import logging
from commons.utils import validar_comando, validar_argumento


class PLCSimulator:
    """
    Simula un PLC con estados y respuestas predefinidas.
    """

    def __init__(self, ip: str, port: int):
        """
        Inicializa el simulador con una dirección IP y puerto ficticios.

        Args:
            ip: Dirección IP ficticia (solo para compatibilidad).
            port: Puerto ficticio (solo para compatibilidad).
        """
        self.ip = ip
        self.port = port
        self.current_position = random.randint(
            0, 9)  # Posición inicial aleatoria
        self.is_running = False  # Estado inicial: detenido
        self.status_code = 0
        self.sock = None  # Simulación de socket
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Simula la conexión al PLC.

        Returns:
            True si la conexión es exitosa.
        """
        self.logger.info(
            f"Simulando conexión con el PLC en {self.ip}:{self.port}")
        self.sock = type('FakeSocket', (object,), {
            'sendall': self.simulated_sendall,
            '_buffer': b''  # Buffer interno para almacenar datos enviados
        })()
        return True

    def close(self):
        """
        Simula el cierre de la conexión.
        """
        self.logger.info("Simulando cierre de conexión con el PLC...")
        self.sock = None

    def simulated_sendall(self, data: bytes):
        """
        Simula el envío de datos al PLC.

        Args:
            data: Datos enviados al PLC.
        """
        self.sock._buffer += data
        print(f"Datos simulados enviados al PLC: {data}")

    def send_command(self, command: int, argument: int = None) -> dict:
        """
        Simula el envío de un comando al PLC.

        Args:
            command: Código de comando (0-255).
            argument: Argumento opcional (0-255).

        Returns:
            Diccionario con estado y posición simulados.
        """
        validar_comando(command)
        if argument is not None:
            validar_argumento(argument)
        try:
            self.logger.info(
                f"Comando recibido en el simulador: {command}, Argumento: {argument}")
            time.sleep(0.5)  # Simula latencia
            if command == 0:  # Comando STATUS
                self.status_code = self.generate_status()
                position = self.current_position
                self.logger.info(
                    f"Estado simulado: {self.status_code}, Posición: {position}")
                return {'status_code': self.status_code, 'position': position}
            elif command == 1:  # Comando MUEVETE
                if self.is_running:
                    self.logger.warning(
                        "El carrusel ya está en movimiento. Ignorando el comando.")
                    return {'error': 'PLC en movimiento'}
                target_position = argument if argument is not None else 0
                self.is_running = True
                self.status_code |= 0b00000010  # Enciende el bit RUN
                self.logger.info(
                    f"Moviendo el carrusel a la posición {target_position}...")
                time.sleep(2)  # Simula tiempo de movimiento
                self.current_position = target_position
                self.is_running = False
                self.status_code &= 0b11111101  # Apaga el bit RUN
                return {'status_code': self.status_code, 'position': self.current_position}
            else:
                self.status_code = self.generate_status()
                return {'status_code': self.status_code, 'position': self.current_position}
        except Exception as e:
            self.logger.error(f"Error en simulador: {str(e)}")
            return {'error': str(e)}

    def generate_status(self) -> int:
        """
        Genera un código de estado simulado.

        Returns:
            Código de estado simulado (8 bits).
        """
        status_code = random.randint(0, 255)

        # Simula probabilidad de estar en movimiento (30%)
        if random.random() < 0.3:
            self.is_running = True
            status_code |= 0b00000010  # Enciende el bit RUN
        else:
            self.is_running = False
            status_code &= 0b11111101  # Apaga el bit RUN

        # Simula estado READY si no hay errores ni movimiento
        if not self.is_running and (status_code & 0b01111100) == 0:
            status_code |= 0b00000001  # Enciende el bit READY
        else:
            status_code &= 0b11111110  # Apaga el bit READY

        return status_code

    def get_current_status(self) -> dict:
        """
        Obtiene el estado actual del PLC simulado.

        Returns:
            Diccionario con estado y posición simulados.
        """
        self.status_code = self.generate_status()
        return {
            'status_code': self.status_code,
            'position': self.current_position
        }

    def receive_response(self) -> dict:
        """
        Simula la recepción de una respuesta del PLC (para compatibilidad con el controlador real).
        """
        # Simula una respuesta estándar
        return {
            'status_code': self.status_code,
            'position': self.current_position,
            'raw_bytes': [self.status_code, self.current_position]
        }

    def __enter__(self):
        """Permite uso con 'with' para gestión automática de recursos en el simulador"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la conexión simulada al salir del bloque 'with'"""
        self.close()
