"""
Ejemplo de cliente WebSocket para sistemas WMS.

Este archivo muestra cómo conectarse al servidor WebSocket del sistema de carruseles
para recibir actualizaciones en tiempo real y enviar comandos.

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas
Fecha: 2025-03-13
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime


class WMSWebSocketClient:
    """Cliente WebSocket para sistemas WMS."""

    def __init__(self, uri: str = "ws://localhost:8765"):
        """
        Inicializa el cliente WebSocket.

        Args:
            uri: URI del servidor WebSocket
        """
        self.uri = uri
        self.websocket = None
        self.is_connected = False
        self.logger = logging.getLogger("wms_websocket_client")
        self.server_info = None
        self.machines = []

        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    async def connect(self):
        """Conecta al servidor WebSocket."""
        try:
            self.logger.info(f"Conectando a {self.uri}...")
            self.websocket = await websockets.connect(self.uri)
            self.is_connected = True
            self.logger.info("Conexión WebSocket establecida")

            # Iniciar listener de mensajes
            asyncio.create_task(self.message_listener())

        except Exception as e:
            self.logger.error(f"Error conectando: {e}")
            raise

    async def disconnect(self):
        """Desconecta del servidor WebSocket."""
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
            self.is_connected = False
            self.logger.info("Desconectado del servidor WebSocket")

    async def send_message(self, message: dict):
        """Envía un mensaje al servidor."""
        if not self.is_connected or not self.websocket:
            raise ConnectionError("No hay conexión WebSocket activa")

        message_json = json.dumps(message)
        await self.websocket.send(message_json)
        self.logger.info(f"Mensaje enviado: {message['type']}")

    async def message_listener(self):
        """Escucha mensajes del servidor."""
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
            self.logger.info("Conexión cerrada por el servidor")
        except Exception as e:
            self.logger.error(f"Error en message_listener: {e}")

    async def handle_message(self, message: str):
        """Maneja mensajes recibidos del servidor."""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "welcome":
                await self.handle_welcome(data)
            elif message_type == "status_broadcast":
                await self.handle_status_broadcast(data)
            elif message_type == "command_executed":
                await self.handle_command_executed(data)
            elif message_type == "machine_status":
                await self.handle_machine_status(data)
            elif message_type == "command_result":
                await self.handle_command_result(data)
            elif message_type == "error":
                await self.handle_error(data)
            elif message_type == "pong":
                self.logger.info("Pong recibido del servidor")
            else:
                self.logger.warning(
                    f"Tipo de mensaje no reconocido: {message_type}")

        except json.JSONDecodeError:
            self.logger.error(f"Mensaje JSON inválido recibido: {message}")
        except Exception as e:
            self.logger.error(f"Error manejando mensaje: {e}")

    async def handle_welcome(self, data: dict):
        """Maneja mensaje de bienvenida."""
        self.server_info = data.get("server_info", {})
        self.machines = data.get("machines", [])
        mode = data.get("mode", "unknown")

        self.logger.info(f"Bienvenida recibida - Modo: {mode}")
        self.logger.info(
            f"Servidor versión: {self.server_info.get('version', 'N/A')}")

        if self.machines:
            self.logger.info(f"Máquinas disponibles: {len(self.machines)}")
            for machine in self.machines:
                self.logger.info(
                    f"  - {machine['id']}: {machine['name']} ({machine['ip']}:{machine['port']})")

    async def handle_status_broadcast(self, data: dict):
        """Maneja broadcast de estado."""
        status = data.get("status", {})
        timestamp = data.get("timestamp")

        if isinstance(status, dict) and "position" in status:
            # Modo single-PLC
            self.logger.info(
                f"Estado PLC - Posición: {status['position']}, Estado: {status.get('status', {})}")
        else:
            # Modo multi-PLC
            self.logger.info(f"Estado Multi-PLC recibido a las {timestamp}:")
            for machine_id, machine_status in status.items():
                if "error" in machine_status:
                    self.logger.warning(
                        f"  {machine_id}: ERROR - {machine_status['error']}")
                else:
                    pos = machine_status.get("position", "N/A")
                    self.logger.info(f"  {machine_id}: Posición {pos}")

    async def handle_command_executed(self, data: dict):
        """Maneja notificación de comando ejecutado por otro cliente."""
        machine_id = data.get("machine_id", "N/A")
        command = data.get("command")
        argument = data.get("argument")
        timestamp = data.get("timestamp")

        self.logger.info(f"Comando ejecutado por otro cliente:")
        self.logger.info(f"  Máquina: {machine_id}")
        self.logger.info(f"  Comando: {command}({argument})")
        self.logger.info(f"  Timestamp: {timestamp}")

    async def handle_machine_status(self, data: dict):
        """Maneja respuesta de estado de máquina específica."""
        machine_id = data.get("machine_id")
        status = data.get("status", {})

        self.logger.info(f"Estado de {machine_id}:")
        self.logger.info(f"  Posición: {status.get('position', 'N/A')}")
        self.logger.info(f"  Estado: {status.get('status', {})}")

    async def handle_command_result(self, data: dict):
        """Maneja resultado de comando enviado."""
        machine_id = data.get("machine_id", "N/A")
        command = data.get("command")
        result = data.get("result", {})

        self.logger.info(f"Resultado de comando {command} en {machine_id}:")
        self.logger.info(f"  Resultado: {result}")

    async def handle_error(self, data: dict):
        """Maneja mensajes de error."""
        error = data.get("error", "Error desconocido")
        timestamp = data.get("timestamp")

        self.logger.error(f"Error del servidor: {error} ({timestamp})")

    # Métodos de conveniencia para WMS

    async def ping(self):
        """Envía ping al servidor."""
        await self.send_message({
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        })

    async def get_status(self, machine_id: str = None):
        """Solicita estado de una máquina específica o todas."""
        message = {
            "type": "get_status",
            "timestamp": datetime.now().isoformat()
        }

        if machine_id:
            message["machine_id"] = machine_id

        await self.send_message(message)

    async def send_command(self, command: int, argument: int = None, machine_id: str = None):
        """Envía comando a una máquina."""
        message = {
            "type": "send_command",
            "command": command,
            "timestamp": datetime.now().isoformat()
        }

        if argument is not None:
            message["argument"] = argument

        if machine_id:
            message["machine_id"] = machine_id

        await self.send_message(message)

    async def move_to_position(self, position: int, machine_id: str):
        """Mueve una máquina a una posición específica (comando 1)."""
        await self.send_command(1, position, machine_id)

    async def subscribe_to_updates(self, subscription_type: str = "status_updates"):
        """Se suscribe a actualizaciones del servidor."""
        await self.send_message({
            "type": "subscribe",
            "subscription_type": subscription_type,
            "timestamp": datetime.now().isoformat()
        })


async def example_wms_interaction():
    """Ejemplo de interacción de un sistema WMS."""
    client = WMSWebSocketClient("ws://localhost:8765")

    try:
        # Conectar al servidor
        await client.connect()

        # Esperar mensaje de bienvenida
        await asyncio.sleep(1)

        # Suscribirse a actualizaciones
        await client.subscribe_to_updates()

        # Hacer ping
        await client.ping()
        await asyncio.sleep(1)

        # Obtener estado de todas las máquinas
        await client.get_status()
        await asyncio.sleep(2)

        # Si hay máquinas disponibles, interactuar con la primera
        if client.machines:
            first_machine = client.machines[0]["id"]

            # Obtener estado específico
            await client.get_status(first_machine)
            await asyncio.sleep(1)

            # Mover a posición 3
            await client.move_to_position(3, first_machine)
            await asyncio.sleep(2)

            # Obtener estado después del movimiento
            await client.get_status(first_machine)
            await asyncio.sleep(1)

        # Mantener conexión activa para recibir broadcasts
        print("Manteniendo conexión activa. Presiona Ctrl+C para salir...")
        while client.is_connected:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nDesconectando...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(example_wms_interaction())
