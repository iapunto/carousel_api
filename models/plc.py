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

    def send_command(self, command: int, argument: int = None):
        """
        Envía un comando al PLC con formato binario.

        Args:
            command: Entero de 8 bits (0-255).
            argument: Opcional - Entero de 8 bits (0-255).

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
            # Empaquetar comando y argumento en bytes
            data = bytes([command])  # Convierte el comando a bytes
            if argument is not None:
                data += bytes([argument])  # Agrega el argumento como bytes
            
            self.sock.sendall(data)  # Enviar datos como bytes
            print(f"Comando enviado: {command}, Argumento: {argument}")
        except Exception as e:
            self.close()
            raise RuntimeError(f"Error enviando datos: {str(e)}")

    def receive_response(self):
        """
        Recibe la respuesta del PLC.

        Returns:
            Un diccionario con el código de estado y la posición del PLC, o None si ocurre un error.
        """
        if not self.sock:
            raise RuntimeError("No hay conexión activa con el PLC")
        
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

    def get_current_status(self):
        """
        Obtiene el estado actual del PLC.

        Returns:
            Diccionario con estado y posición actuales.
        """
        if not self.connect():
            raise RuntimeError("No se pudo conectar al PLC")
        
        try:
            self.send_command(0)  # Comando STATUS
            time.sleep(0.5)
            response = self.receive_response()
            return {
                'status_code': response['status_code'],
                'position': response['position']
            }
        except Exception as e:
            self.close()
            raise RuntimeError(f"Error al obtener el estado del PLC: {str(e)}")