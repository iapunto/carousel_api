"""
Controlador para el carrusel vertical de almacenamiento.

Autor: IA Punto: Soluciones Integrales de Tecnología y Marketing
Proyecto para: INDUSTRIAS PICO S.A.S
Dirección: MEng. Sergio Lankaster Rondón Melo
Colaboración: Ing. Francisco Garnica
Fecha de creación: 2023-09-13
Última modificación: 2024-09-16
"""

from commons.utils import interpretar_estado_plc
import time

class CarouselController:
    """
    Maneja la lógica de control del carrusel, incluyendo el envío de comandos y la interpretación de respuestas del PLC.
    """

    def __init__(self, plc):
        """
        Inicializa el controlador con una instancia de la clase PLC.
        """
        self.plc = plc

    def send_command(self, command: int, argument: int = None):
        """
        Envía un comando al PLC y maneja la respuesta.

        Args:
            command: El comando a enviar (un entero entre 0-255).
            argument: Opcional - El argumento a enviar (un entero entre 0-255).
        """
        if not self.plc.connect():
            print("No se pudo conectar al PLC. Verifica la configuración.")
            return

        try:
            # Envía el comando STATUS para obtener el estado actual
            self.plc.send_command(0)
            time.sleep(0.2)

            # Recibe y muestra el estado actual del PLC
            response = self.plc.receive_response()
            if response:
                self.print_plc_status(response['status_code'])
                print(f"Posición actual del carrusel: {response['position']}")
            else:
                print("No se recibió respuesta al comando STATUS.")
                return

            # Verifica si el PLC está listo para moverse
            if not self.is_plc_ready_to_move(response['status_code']):
                print("El PLC no está en el estado adecuado para moverse.")
                return

            # Envía el comando principal y argumento si es necesario
            if command == 1:  # Comando MUEVETE
                if argument is None or not (0 <= argument <= 9):
                    print("Error: Argumento inválido o fuera de rango (0-9).")
                    return

                # Envía el comando y el argumento como bytes
                self.plc.send_command(command, argument)
                print(f"Comando enviado: {command}, Argumento: {argument}")  # Mensaje de depuración
                time.sleep(0.5)

                # Recibe la respuesta al comando MUEVETE
                move_response = self.plc.receive_response()
                if move_response:
                    print(f"Respuesta al comando MUEVETE: {move_response}")
                else:
                    print("No se recibió respuesta al comando MUEVETE.")
            else:
                # Para otros comandos, envía solo el comando
                self.plc.send_command(command)
                print(f"Comando enviado: {command}, Argumento: None")  # Mensaje de depuración
                time.sleep(0.5)

                # Recibe la respuesta al comando
                response = self.plc.receive_response()
                if response:
                    print(f"Respuesta al comando {command}: {response}")
                else:
                    print(f"No se recibió respuesta al comando {command}.")

        except Exception as e:
            print(f"Error durante la comunicación con el PLC: {e}")
        finally:
            self.plc.close()

    def monitor_plc_status(self):
        """
        Monitorea continuamente el estado del PLC y lo muestra en la consola.
        """
        if not self.plc.connect():
            print("No se pudo conectar al PLC. Verifica la configuración.")
            return

        try:
            while True:
                # Envía el comando STATUS para obtener el estado actual
                self.plc.send_command(0)
                time.sleep(0.2)

                # Recibe y muestra el estado actual del PLC
                response = self.plc.receive_response()
                if response:
                    self.print_plc_status(response['status_code'])
                    print(f"Posición actual del carrusel: {response['position']}")
                else:
                    print("No se recibió respuesta al comando STATUS.")

                time.sleep(1)

        except KeyboardInterrupt:
            print("Monitoreo detenido por el usuario.")
        finally:
            self.plc.close()

    def print_plc_status(self, status_code):
        """
        Imprime el estado del PLC de forma legible.
        """
        estados_plc = interpretar_estado_plc(status_code)
        print(f"Estado del PLC (binario): {format(status_code, '08b')}")
        for nombre_estado, descripcion in estados_plc.items():
            print(f"{nombre_estado}: {descripcion}")

    def is_plc_ready_to_move(self, status_code):
        """
        Verifica si el PLC está en el estado adecuado para moverse.
        """
        estados_plc = interpretar_estado_plc(status_code)
        return (
            estados_plc['READY'] == 'El equipo está listo para operar' and
            estados_plc['RUN'] == 'El equipo está detenido' and
            estados_plc['MODO_OPERACION'] == 'Remoto' and
            estados_plc['ALARMA'] == 'No hay alarma' and
            estados_plc['PARADA_EMERGENCIA'] == 'Sin parada de emergencia' and
            estados_plc['VFD'] == 'El variador de velocidad está OK' and
            estados_plc['ERROR_POSICIONAMIENTO'] == 'No hay error de posicionamiento'
        )