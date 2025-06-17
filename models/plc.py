"""
Clase PLC para comunicación con PLC Delta AS Series vía sockets TCP/IP.

Permite enviar comandos y recibir estados del PLC industrial, con manejo de reintentos y backoff exponencial.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha: 2024-09-27
"""

import socket
import struct
import time
import logging
import random
from commons.utils import validar_comando, validar_argumento


class PLC:
    """
    Encapsula la lógica de comunicación con el PLC Delta AS Series.
    """

    def __init__(self, ip: str, port: int):
        """
        Inicializa el cliente TCP/IP para el PLC.

        Args:
            ip: Dirección IP del PLC (ej: '192.168.1.100').
            port: Puerto de comunicación (típicamente 5000).
        """
        self.ip = ip
        self.port = port
        self.sock = None
        self.timeout = 5.0  # Timeout en segundos [[8]]
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.base_backoff = 0.5  # segundos

    def __enter__(self):
        """Permite uso con 'with' para gestión automática de recursos"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del bloque 'with'"""
        self.close()

    def connect(self) -> bool:
        """
        Establece conexión TCP/IP con el PLC con reintentos y backoff exponencial.
        Returns:
            True si la conexión es exitosa, False en caso contrario.
        """
        if self.sock:
            return True  # Ya conectado

        for attempt in range(1, self.max_retries + 1):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(self.timeout)
                self.sock.connect((self.ip, self.port))
                self.logger.info(
                    f"Conexión establecida con el PLC en {self.ip}:{self.port}")
                return True
            except (socket.timeout, ConnectionRefusedError, OSError) as e:
                self.logger.warning(
                    f"Intento {attempt}: Error de conexión con el PLC: {str(e)}")
                self.close()
                if attempt < self.max_retries:
                    backoff = self.base_backoff * \
                        (2 ** (attempt - 1)) + random.uniform(0, 0.2)
                    time.sleep(backoff)
        self.logger.error(
            f"No se pudo conectar al PLC tras {self.max_retries} intentos.")
        return False

    def close(self):
        """Cierra la conexión de forma segura"""
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except OSError:
                pass  # Ignorar errores si ya estaba cerrado
            finally:
                self.sock = None

    def send_command(self, command: int, argument: int = None) -> bool:
        """
        Envía un comando al PLC con reintentos y backoff exponencial.
        """
        validar_comando(command)
        if argument is not None:
            validar_argumento(argument)
        if not self.sock:
            raise RuntimeError("No hay conexión activa con el PLC")
        for attempt in range(1, self.max_retries + 1):
            try:
                data = struct.pack('B', command)
                if argument is not None:
                    data += struct.pack('B', argument)
                self.sock.sendall(data)
                return True
            except (socket.timeout, BrokenPipeError, OSError) as e:
                self.logger.warning(
                    f"Intento {attempt}: Error enviando datos al PLC: {str(e)}")
                self.close()
                if attempt < self.max_retries:
                    if self.connect():
                        backoff = self.base_backoff * \
                            (2 ** (attempt - 1)) + random.uniform(0, 0.2)
                        time.sleep(backoff)
                        continue
                raise RuntimeError(f"Error enviando datos: {str(e)}")

    def receive_response(self) -> dict:
        """
        Recibe respuesta del PLC (lee hasta 16 bytes para depuración).
        """
        if not self.sock:
            raise RuntimeError("No hay conexión activa")
        for attempt in range(1, self.max_retries + 1):
            try:
                data = self.sock.recv(16)  # Leer hasta 16 bytes
                if len(data) < 2:
                    raise RuntimeError("Respuesta incompleta del PLC")
                # Log de todos los bytes recibidos
                self.logger.info(
                    f"[PLC][DEPURACION] Bytes recibidos: {[b for b in data]} (hex: {[hex(b) for b in data]})")
                # Por compatibilidad, sigue retornando los dos primeros
                status = data[0]
                position = data[1] if len(data) > 1 else 0
                return {
                    'status_code': status,
                    'position': position,
                    'raw_bytes': list(data)
                }
            except (socket.timeout, struct.error, OSError) as e:
                self.logger.warning(
                    f"Intento {attempt}: Error recibiendo datos del PLC: {str(e)}")
                self.close()
                if attempt < self.max_retries:
                    if self.connect():
                        backoff = self.base_backoff * \
                            (2 ** (attempt - 1)) + random.uniform(0, 0.2)
                        time.sleep(backoff)
                        continue
                raise RuntimeError(f"Error recibiendo datos: {str(e)}")

    def get_current_status(self) -> dict:
        """
        Obtiene el estado actual del PLC (status y posición).

        Returns:
            Diccionario con 'status_code' y 'position'.
            Si ocurre un error, retorna {'error': <mensaje>}.
        """
        try:
            if not self.sock:
                self.connect()
            self.send_command(0)  # Comando STATUS
            time.sleep(0.2)  # Pequeña espera para respuesta
            response = self.receive_response()
            return response
        except Exception as e:
            self.logger.error(f"Error en get_current_status: {str(e)}")
            return {'error': str(e)}
