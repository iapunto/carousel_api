"""
Clase PLC para comunicación con PLC Delta AS Series vía sockets TCP/IP.

Autor: IA Punto: Soluciones Integrales de Tecnología y Marketing
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha: 2024-09-27
"""

import socket
import struct
import time


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

    def __enter__(self):
        """Permite uso con 'with' para gestión automática de recursos"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del bloque 'with'"""
        self.close()

    def connect(self) -> bool:
        """
        Establece conexión TCP/IP con el PLC.

        Returns:
            True si la conexión es exitosa, False en caso contrario.
        """
        if self.sock:
            return True  # Ya conectado

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.ip, self.port))
            return True
        except (socket.timeout, ConnectionRefusedError) as e:
            print(f"Error de conexión: {str(e)}")
            self.close()
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
        Envía un comando al PLC con formato binario.

        Args:
            command: Entero de 8 bits (0-255).
            argument: Opcional - Entero de 8 bits (0-255).

        Returns:
            True si el envío fue exitoso.

        Raises:
            ValueError: Si los valores están fuera de rango.
            RuntimeError: Si hay error de comunicación.
        """
        if not (0 <= command <= 255):
            raise ValueError("Comando debe ser entre 0-255")

        if argument is not None and not (0 <= argument <= 255):
            raise ValueError("Argumento debe ser entre 0-255")

        if not self.sock:
            raise RuntimeError("No hay conexión activa con el PLC")

        try:
            # Empaquetar comando y argumento en bytes [[3]]
            data = struct.pack('B', command)
            if argument is not None:
                data += struct.pack('B', argument)
            self.sock.sendall(data)
            print(f"Datos enviados al PLC: {data}")
            return True
        except (socket.timeout, BrokenPipeError) as e:
            self.close()
            raise RuntimeError(f"Error enviando datos: {str(e)}")

    def receive_response(self) -> dict:
        """
        Recibe respuesta del PLC (2 bytes: estado y posición).

        Returns:
            Diccionario con 'status_code' y 'position'.

        Raises:
            RuntimeError: Si hay error de recepción.
        """
        if not self.sock:
            raise RuntimeError("No hay conexión activa")

        try:
            # Recibir exactamente 2 bytes [[6]]
            data = self.sock.recv(2)
            print(f"Datos recibidos del PLC: {data}")
            if len(data) < 2:
                raise RuntimeError("Respuesta incompleta del PLC")

            status, position = struct.unpack('BB', data)
            return {
                'status_code': status,
                'position': position
            }
        except (socket.timeout, struct.error) as e:
            self.close()
            raise RuntimeError(f"Error recibiendo datos: {str(e)}")

    def get_current_status(self):
        """
        Obtiene el estado actual del PLC.
        Returns:
            dict: Estado del PLC con 'status_code' y 'position'.
        """
        try:
            self.connect()
            self.send_command(0)  # Comando STATUS
            time.sleep(2)  # Espera para recibir la respuesta
            response = self.receive_response()
            return response
        except Exception as e:
            print(f"Error al obtener el estado del PLC: {e}")
            return {"status_code": None, "position": None}
