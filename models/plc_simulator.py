import time
import random

class PLCSimulator:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.current_position = random.randint(0, 9)  # Posición inicial aleatoria
        self.is_running = False  # Estado inicial: detenido
        self.status_code = 0
        self.sock = None  # Inicializa el atributo sock a None

    def connect(self):
        print("Simulando conexión con el PLC...")
       # Crea un objeto "falso" que simule un socket
        self.sock = type('FakeSocket', (object,), {
            'sendall': self.simulated_sendall,
            '_buffer': b''  # Buffer interno para almacenar los datos enviados
        })()
        return True

    def close(self):
        print("Simulando cierre de conexión con el PLC...")
        self.sock = None  # Restablece el valor ficticio para simular el cierre
    
    def simulated_sendall(self, data):
        """
        Simula el envío de datos al PLC, almacenándolos en un buffer interno.
        """
        self.sock._buffer += data
        print(f"Datos simulados enviados al PLC: {data}")

    def send_command(self, command):
        if not self.sock:
            raise Exception("No hay conexión establecida con el PLC.")
        
        print(f"Comando recibido en el simulador: {command}")
        time.sleep(1)  # Simula un pequeño retraso

        if command == 0:  # Comando STATUS
            # Genera un estado aleatorio, pero con cierta probabilidad de estar en movimiento
            status_code = random.randint(0, 255)
            if random.random() < 0.3:  # 30% de probabilidad de estar en movimiento
                self.is_running = True
                status_code |= 0b00000010  # Enciende el bit 1 (RUN)
            else:
                self.is_running = False
                status_code &= 0b11111101  # Apaga el bit 1 (RUN)

            # Asegúrate de que READY solo esté activo si no hay errores ni movimiento
            if not self.is_running and status_code & 0b01111100 == 0:
                status_code |= 0b00000001  # Enciende el bit 0 (READY)
            else:
                status_code &= 0b11111110  # Apaga el bit 0 (READY)

            # Envía el estado como un solo byte
            self.sock.sendall(bytes([status_code]))

            # Envía la posición actual del carrusel (asumiendo 1 byte)
            self.sock.sendall(bytes([self.current_position]))

            return {'status_code': status_code, 'position': self.current_position}

        elif isinstance(command, bytes) and len(command) == 2:  # Comando MUEVETE con argumento
            command_byte, argument_byte = command  # Desempaqueta los bytes

            if command_byte == 1:  # Verifica que el comando sea MUEVETE
                try:
                    target_position = int(argument_byte)
                    if 0 <= target_position <= 9:
                        if not self.is_running:
                            self.is_running = True
                            self.status_code |= 0b00000010  # Enciende el bit 1 (RUN)
                            print(f"Moviendo el carrusel a la posición {target_position}...")
                            time.sleep(2)
                            self.current_position = target_position
                            self.is_running = False
                            self.status_code &= 0b11111101  # Apaga el bit 1 (RUN)
                        else:
                            print("El carrusel ya está en movimiento. Ignorando el comando.")
                    else:
                        print("Error: Número de bucket inválido.")
                except ValueError:
                    print("Error: Argumento inválido para el comando MUEVETE.")

        else:
            # Genera un nuevo estado aleatorio para cualquier otro comando
            self.status_code = self.receive_status()
    
    def send_argument(self, argument):
        print(f"Argumento recibido en el simulador: {argument}")
        time.sleep(1)

        if self.is_running:
            print("El carrusel ya está en movimiento. Ignorando el comando.")
            return

        try:
            target_position = int(argument)
            if 0 <= target_position <= 9:
                # Simula el movimiento del carrusel
                print(f"Moviendo el carrusel a la posición {target_position}...")
                time.sleep(2)  # Simula el tiempo de movimiento
                self.current_position = target_position
            else:
                print("Error: Número de bucket inválido.")
        except ValueError:
            print("Error: Argumento inválido.")

    def receive_status(self):
        # Genera un estado aleatorio, pero con cierta probabilidad de estar en movimiento
        status_code = random.randint(0, 255)
        if random.random() < 0.3:  # 30% de probabilidad de estar en movimiento
            self.is_running = True
            status_code |= 0b00000010  # Enciende el bit 1 (RUN)
        else:
            self.is_running = False
            status_code &= 0b11111101  # Apaga el bit 1 (RUN)

        # Asegúrate de que READY solo esté activo si no hay errores ni movimiento
        if not self.is_running and status_code & 0b01111100 == 0:
            status_code |= 0b00000001  # Enciende el bit 0 (READY)
        else:
            status_code &= 0b11111110  # Apaga el bit 0 (READY)

        return status_code

    def receive_position(self):
        return self.current_position

    def send_argument(self, argument):
        print(f"Argumento recibido en el simulador: {argument}")
        time.sleep(1)

        if self.is_running:
            print("El carrusel ya está en movimiento. Ignorando el comando.")
            return

        try:
            target_position = int(argument)
            if 0 <= target_position <= 9:
                # Simula el movimiento del carrusel
                print(f"Moviendo el carrusel a la posición {target_position}...")
                time.sleep(2) 
                self.current_position = target_position
            else:
                print("Error: Número de bucket inválido.")
        except ValueError:
            print("Error: Argumento inválido.")

    def send_command_and_receive_response(self, command):
        print(f"Comando recibido en el simulador: {command}")
        time.sleep(1)  # Simula un pequeño retraso en la respuesta

        if command == 0:  # Comando STATUS
            self.status_code = self.receive_status()
            return {'status_code': self.status_code, 'position': self.current_position}

        elif command == 1:  # Comando MUEVETE
            # ... (lógica para simular el movimiento del carrusel ya implementada en send_argument)
            self.status_code = self.receive_status()
            return {'status_code': self.status_code, 'position': self.current_position} 

        else:
            # Para cualquier otro comando, devuelve el estado actual y la posición
            self.status_code = self.receive_status()
            return {'status_code': self.status_code, 'position': self.current_position}
    
    def receive_response(self):
        """
        Simula la recepción de una respuesta del PLC.

        Returns:
            Un diccionario con el código de estado y la posición del PLC.
        """

        time.sleep(1)  # Simula un pequeño retraso en la respuesta

        # Genera un estado aleatorio, pero con cierta probabilidad de estar en movimiento
        self.status_code = random.randint(0, 255)
        if random.random() < 0.3:  # 30% de probabilidad de estar en movimiento
            self.is_running = True
            self.status_code |= 0b00000010  # Enciende el bit 1 (RUN)
        else:
            self.is_running = False
            self.status_code &= 0b11111101  # Apaga el bit 1 (RUN)

        # Asegúrate de que READY solo esté activo si no hay errores ni movimiento
        if not self.is_running and self.status_code & 0b01111100 == 0:
            self.status_code |= 0b00000001  # Enciende el bit 0 (READY)
        else:
            self.status_code &= 0b11111110  # Apaga el bit 0 (READY)

        return {
            'status_code': self.status_code,
            'position': self.current_position
        }