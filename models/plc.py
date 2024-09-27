"""
Clase PLC para la comunicación con el PLC Delta AS Series a través de sockets.

Autor: IA Punto: Soluciones Integrales de Tecnología y Marketing
Proyecto para: INDUSTRIAS PICO S.A.S
Dirección: MEng. Sergio Lankaster Rondón Melo
Colaboración: Ing. Francisco Garnica
Fecha de creación: 2023-09-13
Última modificación: 2024-09-16
"""

import socket
import struct

class PLC:
    """
    Encapsula la lógica para establecer la conexión con el PLC, enviar comandos y recibir respuestas.
    """

    def __init__(self, ip, port):
        """
        Inicializa la clase PLC con la dirección IP y el puerto del PLC.
        """
        self.ip = ip
        self.port = port
        self.sock = None

    def connect(self):
        """
        Intenta establecer una conexión TCP/IP con el PLC.

        Returns:
            True si la conexión es exitosa, False en caso contrario.
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            print("Conexión exitosa al PLC!")
            return True
        except ConnectionRefusedError:
            print(f"Error: No se pudo establecer la conexión con el PLC en {self.ip}:{self.port}.")
            return False

    def close(self):
        """
        Cierra la conexión con el PLC si está abierta.
        """
        if self.sock:
            print("Cerrando la conexión...")
            self.sock.close()
            print("Conexión cerrada")

    def send_command(self, command):
        """
        Envía un comando al PLC.

        Args:
            command: El comando a enviar (un entero que representa un byte).
        """

        if not self.sock:
            raise Exception("No hay conexión establecida con el PLC.")

        try:
            # Envía el comando como un solo byte
            self.sock.sendall(command)

        except Exception as e:
            print(f"Error al enviar datos al PLC: {e}")

    def receive_response(self):
        """
        Recibe la respuesta del PLC.

        Returns:
            Un diccionario con el código de estado y la posición del PLC, o None si ocurre un error.
        """

        if not self.sock:
            raise Exception("No hay conexión establecida con el PLC.")

        try:
            # Recibe la respuesta (1 byte para estado y 1 para posición)
            status_data = self.sock.recv(1)
            position_data = self.sock.recv(1)

            if status_data and position_data:
                status_code = status_data[0]
                position = position_data[0]

                return {
                    'status_code': status_code,
                    'position': position
                }  # Devuelve un diccionario
            else:
                print("No se recibió respuesta completa del PLC.")
                return None

        except socket.timeout:
            print("Error: Timeout al intentar comunicarse con el PLC.")
            return None
        except Exception as e:
            print(f"Ocurrió un error inesperado al recibir datos: {e}")
            return None

    def send_argument(self, argument):
        """
        Envía un argumento al PLC.

        Args:
            argument: El argumento a enviar (un entero que representa un byte).
        """

        if not self.sock:
            raise Exception("No hay conexión establecida con el PLC.")

        try:
            # Envía el argumento como un solo byte
            self.sock.sendall(bytes([argument])) 

        except Exception as e:
            print(f"Error al enviar datos al PLC: {e}")