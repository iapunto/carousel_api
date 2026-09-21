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
import os
from logging.handlers import RotatingFileHandler

# Configuración de bitácora de operaciones
operations_logger = logging.getLogger("operations")
if not operations_logger.hasHandlers():
    log_folder = os.path.join(
        os.getenv('LOCALAPPDATA'), 'Vertical PIC', 'logs')
    os.makedirs(log_folder, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_folder, "operations.log"), maxBytes=500_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    operations_logger.addHandler(handler)
    operations_logger.setLevel(logging.INFO)


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
        self.response_delay = 3.0  # Tiempo de espera para la respuesta del PLC en segundos

    def send_command(self, command: int, argument: int = None, remote_addr=None) -> dict:
        """
        Envía un comando al PLC y registra en la bitácora de operaciones.

        Args:
            command: Código de comando (0-255)
            argument: Argumento opcional (0-255)
            remote_addr: Dirección IP o proceso remoto

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
                # Comando 1 (mover) es 1-indexado en la API, 0-indexado en el PLC
                plc_argument = argument - 1 if command == 1 and argument is not None else argument
                self.logger.info(
                    f"[PLC] Enviando comando: {command}, argumento: {argument} (PLC: {plc_argument})")
                self.plc.send_command(command, plc_argument)
                # Pausa para dar tiempo al PLC a procesar el comando antes de responder
                time.sleep(self.response_delay)
                response = self.plc.receive_response()
                # Si es comando de movimiento, el PLC responde con un ACK (21)
                # Necesitamos esperar a que termine el movimiento y consultar el estado real
                if command == 1:
                    self.logger.info("[PLC] Comando de movimiento: esperando a que termine...")
                    time.sleep(5)  # Dar tiempo al movimiento físico
                    # Consultar estado real después del movimiento
                    try:
                        self.plc.send_command(0)  # Comando STATUS
                        time.sleep(1)
                        final_response = self.plc.receive_response()
                        self.logger.info(
                            f"[PLC] Estado final después de movimiento: {final_response}")
                        response = final_response
                    except Exception as e:
                        self.logger.warning(f"[PLC] No se pudo consultar estado final: {e}")
            # Log de bajo nivel: datos crudos recibidos
            status_code = response['status_code']
            position = response['position']
            # Formato binario de 8 bits
            status_bin = format(status_code, '08b')
            # Diccionario bit a bit
            status_bits = {f'bit_{i}': (
                status_code >> i) & 1 for i in range(7, -1, -1)}
            self.logger.info(
                f"[PLC][RAW] status_code: {status_code} (bin: {status_bin}), bits: {status_bits}, position: {position}")
            self.logger.info(f"[PLC][RAW] Respuesta cruda: {response}")
            status = interpretar_estado_plc(response['status_code'])
            self.logger.info(
                f"[PLC] Respuesta recibida: status_code={response['status_code']}, position={response['position']}")
            operations_logger.info(
                f"[COMANDO] IP/Proceso: {remote_addr} | Comando: {command} | Argumento: {argument} | Resultado: OK")
            return {
                'status': status,
                'position': response['position'] + 1,
                'raw_status': response['status_code']
            }
        except Exception as e:
            self.logger.error(
                f"[PLC] Error en send_command (comando={command}, argumento={argument}): {str(e)}")
            operations_logger.error(
                f"[COMANDO] IP/Proceso: {remote_addr} | Comando: {command} | Argumento: {argument} | Resultado: ERROR | Error: {str(e)}")
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
            target: Posición objetivo (1-indexada, 1 = primer cangilón)

        Returns:
            Respuesta del PLC
        """
        if not (1 <= target <= 255):
            raise ValueError("Posición debe estar entre 1 y 255")

        return self.send_command(1, target - 1)  # Comando 1 = MUEVETE (PLC es 0-indexado)

    def verify_ready_state(self) -> bool:
        """
        Verifica si el PLC está listo para operar.

        Returns:
            True si el PLC está en estado READY
        """
        status = self.get_current_status()['status']
        return status.get('READY', '') == 'El equipo está listo para operar'
