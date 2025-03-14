import time


class CommandHandler:
    def __init__(self):
        self.last_command_time = 0  # Tiempo del último comando enviado
        self.lock_duration = 3      # Duración del bloqueo en segundos

    def can_send_command(self):
        """
        Verifica si se puede enviar un nuevo comando.
        Returns:
            bool: True si se puede enviar un comando, False si está bloqueado.
        """
        current_time = time.time()
        if current_time - self.last_command_time < self.lock_duration:
            print("Bloqueado: Espera 3 segundos antes de enviar otro comando.")
            return False
        return True

    def send_command(self, command, argument=None):
        """
        Envía un comando al PLC si no está bloqueado.
        Args:
            command (str): El comando a enviar.
            argument (str, optional): Argumento adicional para el comando.
        Returns:
            bool: True si el comando se envió, False si está bloqueado.
        """
        if not self.can_send_command():
            return False

        try:
            print(f"Enviando comando: {command}, Argumento: {argument}")
            # Lógica para enviar el comando al PLC aquí
            self.last_command_time = time.time()  # Actualiza el tiempo del último comando
            return True
        except Exception as e:
            print(f"Error al enviar el comando: {str(e)}")
            return False
