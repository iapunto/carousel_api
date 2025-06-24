"""
Servidor WebSocket para comunicación en tiempo real con sistemas WMS.

Permite a los sistemas WMS conectarse vía WebSocket para recibir:
- Actualizaciones de estado en tiempo real
- Notificaciones de cambios de posición
- Alertas del sistema
- Confirmaciones de comandos

Autor: Industrias Pico S.A.S
Desarrollo: IA Punto: Soluciones Tecnológicas
Fecha: 2025-03-13
"""

import asyncio
import json
import logging
import websockets
import threading
import time
from datetime import datetime
from typing import Dict, Set, Optional, Any
from commons.config_manager import ConfigManager
from models.plc_manager import PLCManager
from models.plc import PLC
from controllers.carousel_controller import CarouselController


class WebSocketServer:
    """Servidor WebSocket para comunicación en tiempo real con WMS."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        """
        Inicializa el servidor WebSocket.

        Args:
            host: Dirección IP del servidor
            port: Puerto del servidor WebSocket
        """
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.plc_manager: Optional[PLCManager] = None
        self.carousel_controller: Optional[CarouselController] = None
        self.is_multi_plc = False
        self.logger = logging.getLogger("websocket_server")
        self.running = False
        self.status_broadcast_task = None

        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def initialize(self):
        """Inicializa el servidor según la configuración actual."""
        try:
            config_manager = ConfigManager()

            if config_manager.is_multi_plc_enabled():
                # Modo Multi-PLC
                self.is_multi_plc = True
                self.plc_manager = PLCManager()
                machines = self.plc_manager.get_available_machines()
                self.logger.info(
                    f"Servidor WebSocket iniciado en modo MULTI-PLC con {len(machines)} máquinas")
            else:
                # Modo Single-PLC
                self.is_multi_plc = False
                single_config = config_manager.load_single_config()

                # Crear instancia PLC
                if single_config.get('simulator_enabled', False):
                    from models.plc_simulator import PLCSimulator
                    plc = PLCSimulator()
                    self.logger.info("Usando PLCSimulator para WebSocket")
                else:
                    plc = PLC(single_config['ip'], single_config['port'])
                    self.logger.info(
                        f"Usando PLC real {single_config['ip']}:{single_config['port']} para WebSocket")

                self.carousel_controller = CarouselController(plc)
                self.logger.info(
                    "Servidor WebSocket iniciado en modo SINGLE-PLC")

        except Exception as e:
            self.logger.error(f"Error inicializando servidor WebSocket: {e}")
            raise

    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """Registra un nuevo cliente WebSocket."""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(
            f"Cliente WebSocket conectado: {client_info} - Total clientes: {len(self.clients)}")

        # Enviar mensaje de bienvenida
        welcome_msg = {
            "type": "welcome",
            "timestamp": datetime.now().isoformat(),
            "mode": "multi-plc" if self.is_multi_plc else "single-plc",
            "server_info": {
                "version": "1.0.0",
                "capabilities": ["status_updates", "command_execution", "real_time_notifications"]
            }
        }

        if self.is_multi_plc:
            welcome_msg["machines"] = self.plc_manager.get_available_machines()

        await websocket.send(json.dumps(welcome_msg))

    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """Desregistra un cliente WebSocket."""
        self.clients.discard(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(
            f"Cliente WebSocket desconectado: {client_info} - Total clientes: {len(self.clients)}")

    async def broadcast_message(self, message: Dict[str, Any]):
        """Envía un mensaje a todos los clientes conectados."""
        if not self.clients:
            return

        message_json = json.dumps(message)
        disconnected_clients = set()

        for client in self.clients.copy():
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                self.logger.error(f"Error enviando mensaje a cliente: {e}")
                disconnected_clients.add(client)

        # Limpiar clientes desconectados
        for client in disconnected_clients:
            self.clients.discard(client)

    async def handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Maneja mensajes recibidos de clientes WebSocket."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

            self.logger.info(
                f"Mensaje recibido de {client_info}: {message_type}")

            if message_type == "ping":
                # Responder pong
                await websocket.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))

            elif message_type == "get_status":
                # Obtener estado actual
                await self.handle_status_request(websocket, data)

            elif message_type == "send_command":
                # Ejecutar comando
                await self.handle_command_request(websocket, data)

            elif message_type == "subscribe":
                # Suscribirse a actualizaciones
                await self.handle_subscription_request(websocket, data)

            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Tipo de mensaje no reconocido: {message_type}",
                    "timestamp": datetime.now().isoformat()
                }))

        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "error": "Formato JSON inválido",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            self.logger.error(f"Error manejando mensaje de cliente: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Error interno: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def handle_status_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Maneja solicitudes de estado."""
        try:
            if self.is_multi_plc:
                machine_id = data.get("machine_id")
                if machine_id:
                    # Estado de máquina específica
                    status = self.plc_manager.get_machine_status(
                        machine_id, "websocket")
                    response = {
                        "type": "machine_status",
                        "machine_id": machine_id,
                        "status": status,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # Estado de todas las máquinas
                    machines = self.plc_manager.get_available_machines()
                    all_status = {}
                    for machine in machines:
                        try:
                            all_status[machine["id"]] = self.plc_manager.get_machine_status(
                                machine["id"], "websocket")
                        except Exception as e:
                            all_status[machine["id"]] = {"error": str(e)}

                    response = {
                        "type": "all_machines_status",
                        "status": all_status,
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                # Modo single-PLC
                status = self.carousel_controller.get_current_status()
                response = {
                    "type": "status",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }

            await websocket.send(json.dumps(response))

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Error obteniendo estado: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def handle_command_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Maneja solicitudes de comando."""
        try:
            command = data.get("command")
            argument = data.get("argument")

            if not isinstance(command, int) or not (0 <= command <= 255):
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "El comando debe ser un entero entre 0 y 255",
                    "timestamp": datetime.now().isoformat()
                }))
                return

            if self.is_multi_plc:
                machine_id = data.get("machine_id")
                if not machine_id:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "error": "machine_id requerido en modo multi-PLC",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return

                result = self.plc_manager.send_command_to_machine(
                    machine_id, command, argument, "websocket")
                response = {
                    "type": "command_result",
                    "machine_id": machine_id,
                    "command": command,
                    "argument": argument,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = self.carousel_controller.send_command(
                    command, argument)
                response = {
                    "type": "command_result",
                    "command": command,
                    "argument": argument,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

            await websocket.send(json.dumps(response))

            # Broadcast del comando ejecutado a otros clientes
            broadcast_msg = {
                "type": "command_executed",
                "command": command,
                "argument": argument,
                "timestamp": datetime.now().isoformat()
            }

            if self.is_multi_plc:
                broadcast_msg["machine_id"] = machine_id

            # Enviar a todos los clientes excepto el que envió el comando
            for client in self.clients:
                if client != websocket:
                    try:
                        await client.send(json.dumps(broadcast_msg))
                    except:
                        pass

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "error": f"Error ejecutando comando: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def handle_subscription_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Maneja solicitudes de suscripción."""
        subscription_type = data.get("subscription_type", "status_updates")

        response = {
            "type": "subscription_confirmed",
            "subscription_type": subscription_type,
            "timestamp": datetime.now().isoformat()
        }

        await websocket.send(json.dumps(response))

    async def status_broadcast_loop(self):
        """Loop para broadcast periódico de estado."""
        while self.running:
            try:
                if self.clients:
                    if self.is_multi_plc:
                        # Broadcast estado de todas las máquinas
                        machines = self.plc_manager.get_available_machines()
                        all_status = {}

                        for machine in machines:
                            try:
                                status = self.plc_manager.get_machine_status(
                                    machine["id"], "broadcast")
                                all_status[machine["id"]] = status
                            except Exception as e:
                                all_status[machine["id"]] = {"error": str(e)}

                        broadcast_msg = {
                            "type": "status_broadcast",
                            "status": all_status,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        # Broadcast estado single-PLC
                        status = self.carousel_controller.get_current_status()
                        broadcast_msg = {
                            "type": "status_broadcast",
                            "status": status,
                            "timestamp": datetime.now().isoformat()
                        }

                    await self.broadcast_message(broadcast_msg)

                # Esperar 2 segundos antes del próximo broadcast
                await asyncio.sleep(2)

            except Exception as e:
                self.logger.error(f"Error en status_broadcast_loop: {e}")
                await asyncio.sleep(5)

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Maneja conexiones de clientes WebSocket."""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            self.logger.error(f"Error en handle_client: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Inicia el servidor WebSocket."""
        self.running = True
        self.logger.info(
            f"Iniciando servidor WebSocket en {self.host}:{self.port}")

        # Inicializar configuración
        self.initialize()

        # Iniciar loop de broadcast de estado
        self.status_broadcast_task = asyncio.create_task(
            self.status_broadcast_loop())

        # Iniciar servidor WebSocket
        server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )

        self.logger.info(
            f"Servidor WebSocket ejecutándose en ws://{self.host}:{self.port}")
        return server

    def stop_server(self):
        """Detiene el servidor WebSocket."""
        self.running = False
        if self.status_broadcast_task:
            self.status_broadcast_task.cancel()
        self.logger.info("Servidor WebSocket detenido")


def run_websocket_server(host: str = "0.0.0.0", port: int = 8765):
    """Ejecuta el servidor WebSocket en un loop de eventos."""
    server = WebSocketServer(host, port)

    async def main():
        websocket_server = await server.start_server()
        try:
            await websocket_server.wait_closed()
        except KeyboardInterrupt:
            server.stop_server()

    asyncio.run(main())


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Ejecutar servidor
    run_websocket_server()
