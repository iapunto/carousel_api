"""
Gestor de múltiples PLCs para control de carruseles industriales.

Permite gestionar varios PLCs simultáneamente, cada uno identificado por un ID único.
Incluye logging de conexiones y comandos por cliente.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2025-01-XX
Versión: 1.0.0 - Fase 1
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
                controller.machine_id = machine_id

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
                                argument: int = None, client_ip: str = None,
                                skip_position_check: bool = False) -> Dict[str, Any]:
        """
        Envía un comando a una máquina específica.

        Args:
            machine_id: ID de la máquina
            command: Código de comando (0-255)
            argument: Argumento opcional (0-255)
            client_ip: IP del cliente que envía el comando (para logging)
            skip_position_check: Omitir guardia de misma posición (force)

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
                    command, argument, client_ip,
                    skip_position_check=skip_position_check)

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
                                 client_ip: str = None,
                                 skip_position_check: bool = False) -> Dict[str, Any]:
        """
        Mueve una máquina a una posición específica.

        Args:
            machine_id: ID de la máquina
            target_position: Posición objetivo (0-9)
            client_ip: IP del cliente (para logging)
            skip_position_check: Omitir guardia de misma posición (force)

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
                    target_position,
                    skip_position_check=skip_position_check)

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

    def get_machine_diagnostics(self, machine_id: str,
                                client_ip: str = None) -> Dict[str, Any]:
        """Diagnóstico estilo 'computadora de abordo': estado + fallas
        localizadas + registros físicos del PLC vía Modbus.

        Fuentes:
        - Protocolo :3200 → bits de estado (READY/RUN/MODO/ALARMA/...)
        - Modbus :502 → D0 posición física, D2 target, D4/D6/D10 pasos
        """
        if machine_id not in self.controllers:
            raise ValueError(f"Máquina '{machine_id}' no encontrada")

        result = {
            "machine_id": machine_id,
            "checked_at": datetime.now().isoformat(),
            "online": False,
            "status": {},
            "position": None,
            "target_position": None,
            "position_desync": False,
            "step_counters": {},
            "faults": [],
            "warnings": [],
        }

        controller = self.controllers[machine_id]
        plc_ip = controller.plc.ip

        # 1) Bits de estado por protocolo :3200
        try:
            status_resp = controller.get_current_status()
            result["online"] = True
            result["status"] = status_resp.get("status", {})
            result["raw_status"] = status_resp.get("raw_status")
            if status_resp.get("position") is not None:
                result["position"] = status_resp["position"]
                result["position_source"] = status_resp.get(
                    "position_source")
        except Exception as e:
            result["faults"].append({
                "code": "COMM_FAILURE",
                "severity": "critical",
                "component": "Comunicación :3200",
                "message": f"PLC no responde por socket: {e}",
            })
            return result

        # 2) Registros físicos por Modbus :502
        try:
            from models.modbus_delta import read_registers
            regs = read_registers(plc_ip, 0, 24, timeout=2.0)
            if regs:
                result["registers"] = {
                    "D0_position_real": regs[0],
                    "D2_target": regs[2],
                    "D4_steps_a": regs[4],
                    "D6_steps_b": regs[6],
                    "D8_flag": regs[8],
                    "D10_steps_c": regs[10],
                    "D16_counter": regs[16],
                    "D20_param": regs[20],
                    "D22_target_copy": regs[22],
                }
                result["position"] = regs[0] + 1
                result["target_position"] = regs[2] + 1
                result["position_source"] = "modbus"
                result["position_desync"] = regs[0] != regs[2]
                result["step_counters"] = {
                    "D4": regs[4], "D6": regs[6], "D10": regs[10]}
        except Exception as e:
            result["warnings"].append(
                f"Modbus :502 no disponible, posición por protocolo: {e}")

        # 3) Fallas localizadas a partir de los bits interpretados
        status = result["status"]
        fault_map = {
            "READY": ("no puede operar", "Equipo no listo", "General"),
            "ALARMA": ("alarma activa", "Alarma activa en el equipo",
                       "Panel de alarmas"),
            "PARADA_EMERGENCIA": ("presionada y activa",
                                  "Parada de emergencia activa",
                                  "Botón de paro / barra de seguridad"),
            "VFD": ("error", "Error en el variador de velocidad",
                    "Variador (VFD)"),
            "ERROR_POSICIONAMIENTO": ("ha ocurrido", "Error de posicionamiento",
                                      "Sensores de posición"),
        }
        for key, (needle, message, component) in fault_map.items():
            text = (status.get(key) or "").lower()
            if needle in text:
                result["faults"].append({
                    "code": key, "severity": "error",
                    "component": component, "message": message,
                })
        run_text = (status.get("RUN") or "").lower()
        if "en movimiento" in run_text:
            result["warnings"].append("Equipo en movimiento")
        modo = (status.get("MODO_OPERACION") or "").lower()
        if "manual" in modo:
            result["warnings"].append(
                "Modo Manual — comandos remotos bloqueados")
        if result["position_desync"]:
            result["faults"].append({
                "code": "POSITION_DESYNC",
                "severity": "warning",
                "component": "Contador de posición",
                "message": (
                    f"Comandada ({result['target_position']}) difiere de la "
                    f"física ({result['position']}) — un movimiento fue "
                    "interrumpido o el contador se desfasó"),
            })

        result["fault_count"] = len(result["faults"])
        result["healthy"] = result["online"] and not any(
            f["severity"] == "critical" or f["severity"] == "error"
            for f in result["faults"])
        return result

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

    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de salud de todas las máquinas.

        Returns:
            Diccionario con estado de salud de cada máquina
        """
        health_status = {
            "overall_status": "healthy",
            "machines": {},
            "total_machines": len(self.plc_configs),
            "healthy_machines": 0,
            "unhealthy_machines": 0
        }

        for machine_id in self.controllers.keys():
            try:
                # Intentar obtener estado sin logging detallado
                status = self.controllers[machine_id].get_current_status()
                health_status["machines"][machine_id] = {
                    "status": "healthy",
                    "last_check": datetime.now().isoformat(),
                    "position": status.get("position", "unknown")
                }
                health_status["healthy_machines"] += 1
            except Exception as e:
                health_status["machines"][machine_id] = {
                    "status": "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "error": str(e)
                }
                health_status["unhealthy_machines"] += 1

        # Determinar estado general
        if health_status["unhealthy_machines"] > 0:
            if health_status["healthy_machines"] == 0:
                health_status["overall_status"] = "critical"
            else:
                health_status["overall_status"] = "degraded"

        return health_status
