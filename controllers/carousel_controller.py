"""
Controlador para el carrusel vertical de almacenamiento.

Orquesta la comunicación entre la API y el PLC (real o simulado), interpretando estados y gestionando comandos de alto nivel.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2023-09-13
Última modificación: 2024-09-27
"""

from models.plc import PLC  # Importación explícita del PLC real [[2]]
# Interpretación de estados [[3]]
from commons.utils import interpretar_estado_plc, validar_comando, validar_argumento
import time
import logging


class CarouselController:
    """
    Controlador para operaciones del carrusel con el PLC.
    """

    def __init__(self, plc: PLC):
        """
        Inicializa el controlador con una instancia de PLC.

        Args:
            plc: Instancia de la clase PLC (real o simulador) [[2]]
        """
        self.plc = plc
        self.logger = logging.getLogger(__name__)

    def send_command(self, command: int, argument: int = None) -> dict:
        """
        Envía un comando al PLC y devuelve la respuesta procesada.

        Args:
            command: Código de comando (0-255)
            argument: Argumento opcional (0-255)

        Returns:
            Diccionario con estado y posición

        Raises:
            ValueError: Parámetros inválidos
            RuntimeError: Error de comunicación
        """
        validar_comando(command)
        if argument is not None:
            validar_argumento(argument)
        try:
            with self.plc:  # Gestión automática de conexión [[2]]
                self.plc.send_command(command, argument)
                response = self.plc.receive_response()

            # Interpretar estado [[3]]
            status = interpretar_estado_plc(response['status_code'])
            return {
                'status': status,
                'position': response['position'],
                'raw_status': response['status_code']
            }
        except Exception as e:
            self.logger.error(f"Error en send_command: {str(e)}")
            raise RuntimeError(f"Fallo en comunicación PLC: {str(e)}")

    def get_current_status(self) -> dict:
        """
        Obtiene el estado actual del PLC sin enviar comandos.

        Returns:
            Diccionario con estado y posición
        """
        return self.send_command(0)  # Comando 0 = STATUS

    def move_to_position(self, target: int) -> dict:
        """
        Mueve el carrusel a una posición específica.

        Args:
            target: Posición objetivo (0-9)

        Returns:
            Respuesta del PLC
        """
        if not (0 <= target <= 9):
            raise ValueError("Posición debe estar entre 0-9")

        return self.send_command(1, target)  # Comando 1 = MUEVETE

    def verify_ready_state(self) -> bool:
        """
        Verifica si el PLC está listo para operar.

        Returns:
            True si el PLC está en estado READY
        """
        status = self.get_current_status()['status']
        return status.get('READY', '') == 'El equipo está listo para operar'
