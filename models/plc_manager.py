"""
Gestor de múltiples PLCs para control de carruseles industriales.

Permite gestionar varios PLCs simultáneamente, cada uno identificado por un ID único.
Incluye logging de conexiones y comandos por cliente.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2025-01-XX
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from models.plc import PLC
from models.plc_simulator import PLCSimulator
from controllers.carousel_controller import CarouselController
import os
from logging.handlers import RotatingFileHandler


class PLCManager:
    """
    Gestor centralizado para múltiples PLCs.
    Permite operaciones por ID de máquina y mantiene registro de conexiones.
    """

    def __init__(self, plc_configs: List[Dict[str, Any]]):
        """
        Inicializa el gestor con configuraciones de múltiples PLCs.

        Args:
            plc_configs: Lista de configuraciones de PLC
                        [{"id": "machine_1", "ip": "192.168.1.50", "port": 3200, "name": "Carrusel Principal", "simulator": False}]
        """
        self.plc_configs = plc_configs
        self.plc_instances: Dict[str, PLC] = {}
        self.controllers: Dict[str, CarouselController] = {}
        self.connection_locks: Dict[str, threading.Lock] = {}
        self.logger = logging.getLogger(__name__)

        # Logger específico para conexiones de clientes
        self._setup_connection_logger()

        # Inicializar PLCs
        self._initialize_plcs()

    def _setup_connection_logger(self):
        """Configura el logger específico para conexiones de clientes."""
        self.connection_logger = logging.getLogger("client_connections")
        if not self.connection_logger.hasHandlers():
            log_folder = os.path.join(
                os.getenv('LOCALAPPDATA', '.'), 'Vertical PIC', 'logs')
            os.makedirs(log_folder, exist_ok=True)
            handler = RotatingFileHandler(
                os.path.join(log_folder, "client_connections.log"),
                maxBytes=1_000_000, backupCount=10, encoding="utf-8")
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s')
            handler.setFormatter(formatter)
            self.connection_logger.addHandler(handler)
            self.connection_logger.setLevel(logging.INFO)

    def _initialize_plcs(self):
        """Inicializa todas las instancias de PLC según la configuración."""
        for config in self.plc_configs:
            machine_id = config["id"]
            try:
                # Crear instancia de PLC (real o simulador)
                if config.get("simulator", False):
                    plc_instance = PLCSimulator(config["ip"], config["port"])
                else:
                    plc_instance = PLC(config["ip"], config["port"])

                # Crear controlador para este PLC
                controller = CarouselController(plc_instance)

                # Almacenar referencias
                self.plc_instances[machine_id] = plc_instance
                self.controllers[machine_id] = controller
                self.connection_locks[machine_id] = threading.Lock()

                self.logger.info(
                    f"PLC inicializado: {machine_id} ({config.get('name', 'Sin nombre')}) "
                    f"- IP: {config['ip']}:{config['port']} "
                    f"- Modo: {'Simulador' if config.get('simulator') else 'Real'}")

            except Exception as e:
                self.logger.error(
                    f"Error inicializando PLC {machine_id}: {str(e)}")
                raise

    def get_available_machines(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista de máquinas disponibles.

        Returns:
            Lista con información de todas las máquinas configuradas
        """
        machines = []
        for config in self.plc_configs:
            machines.append({
                "id": config["id"],
                "name": config.get("name", "Sin nombre"),
                "ip": config["ip"],
                "port": config["port"],
                "type": "Simulador" if config.get("simulator") else "Real PLC",
                "status": "available"
            })
        return machines

    def get_machine_status(self, machine_id: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Obtiene el estado de una máquina específica.

        Args:
            machine_id: ID de la máquina
            client_ip: IP del cliente que hace la consulta (para logging)

        Returns:
            Estado de la máquina

        Raises:
            ValueError: Si la máquina no existe
        """
        if machine_id not in self.controllers:
            raise ValueError(f"Máquina '{machine_id}' no encontrada")

        # Log de conexión
        self.connection_logger.info(
            f"STATUS_REQUEST | Cliente: {client_ip or 'Unknown'} | "
            f"Máquina: {machine_id} | Timestamp: {datetime.now().isoformat()}")

        try:
            with self.connection_locks[machine_id]:
                result = self.controllers[machine_id].get_current_status()

            self.connection_logger.info(
                f"STATUS_RESPONSE | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Resultado: OK | "
                f"Estado: {result.get('status', {}).get('READY', 'N/A')}")

            return result

        except Exception as e:
            self.connection_logger.error(
                f"STATUS_ERROR | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Error: {str(e)}")
            raise

    def send_command_to_machine(self, machine_id: str, command: int,
                                argument: int = None, client_ip: str = None) -> Dict[str, Any]:
        """
        Envía un comando a una máquina específica.

        Args:
            machine_id: ID de la máquina
            command: Código de comando (0-255)
            argument: Argumento opcional (0-255)
            client_ip: IP del cliente que envía el comando (para logging)

        Returns:
            Respuesta del PLC

        Raises:
            ValueError: Si la máquina no existe
        """
        if machine_id not in self.controllers:
            raise ValueError(f"Máquina '{machine_id}' no encontrada")

        # Log de comando
        self.connection_logger.info(
            f"COMMAND_REQUEST | Cliente: {client_ip or 'Unknown'} | "
            f"Máquina: {machine_id} | Comando: {command} | "
            f"Argumento: {argument} | Timestamp: {datetime.now().isoformat()}")

        try:
            with self.connection_locks[machine_id]:
                result = self.controllers[machine_id].send_command(
                    command, argument, client_ip)

            self.connection_logger.info(
                f"COMMAND_RESPONSE | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Comando: {command} | "
                f"Argumento: {argument} | Resultado: OK | "
                f"Nueva_posición: {result.get('position', 'N/A')}")

            return result

        except Exception as e:
            self.connection_logger.error(
                f"COMMAND_ERROR | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Comando: {command} | "
                f"Argumento: {argument} | Error: {str(e)}")
            raise

    def move_machine_to_position(self, machine_id: str, target_position: int,
                                 client_ip: str = None) -> Dict[str, Any]:
        """
        Mueve una máquina a una posición específica.

        Args:
            machine_id: ID de la máquina
            target_position: Posición objetivo (0-9)
            client_ip: IP del cliente (para logging)

        Returns:
            Respuesta del PLC
        """
        if machine_id not in self.controllers:
            raise ValueError(f"Máquina '{machine_id}' no encontrada")

        self.connection_logger.info(
            f"MOVE_REQUEST | Cliente: {client_ip or 'Unknown'} | "
            f"Máquina: {machine_id} | Posición_objetivo: {target_position}")

        try:
            with self.connection_locks[machine_id]:
                result = self.controllers[machine_id].move_to_position(
                    target_position)

            self.connection_logger.info(
                f"MOVE_RESPONSE | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Posición_objetivo: {target_position} | "
                f"Resultado: OK")

            return result

        except Exception as e:
            self.connection_logger.error(
                f"MOVE_ERROR | Cliente: {client_ip or 'Unknown'} | "
                f"Máquina: {machine_id} | Posición_objetivo: {target_position} | "
                f"Error: {str(e)}")
            raise

    def get_machine_info(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de configuración de una máquina.

        Args:
            machine_id: ID de la máquina

        Returns:
            Información de la máquina o None si no existe
        """
        for config in self.plc_configs:
            if config["id"] == machine_id:
                return {
                    "id": config["id"],
                    "name": config.get("name", "Sin nombre"),
                    "ip": config["ip"],
                    "port": config["port"],
                    "type": "Simulador" if config.get("simulator") else "Real PLC"
                }
        return None

    def close_all_connections(self):
        """Cierra todas las conexiones de PLC de forma segura."""
        for machine_id, plc in self.plc_instances.items():
            try:
                plc.close()
                self.logger.info(
                    f"Conexión cerrada para máquina: {machine_id}")
            except Exception as e:
                self.logger.error(
                    f"Error cerrando conexión para máquina {machine_id}: {str(e)}")
