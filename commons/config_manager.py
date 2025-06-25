"""
Gestor de configuración para sistema de carruseles industriales.

Permite gestionar configuraciones single-PLC y multi-PLC desde la interfaz gráfica.
Almacena la configuración en archivos JSON locales.

Autor: IA Punto: Soluciones Tecnológicas
Proyecto para: INDUSTRIAS PICO S.A.S
Fecha de creación: 2025-01-XX
Versión: 1.0.0
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil


class ConfigManager:
    """
    Gestor centralizado de configuración para sistemas single-PLC y multi-PLC.
    """

    def __init__(self):
        """Inicializa el gestor de configuración."""
        self.logger = logging.getLogger(__name__)

        # Archivos de configuración
        self.single_config_file = "config.json"
        self.multi_config_file = "config_multi_plc.json"
        self.backup_folder = "config_backups"

        # Configuración por defecto single-PLC
        self.default_single_config = {
            "ip": "192.168.1.50",
            "port": 3200,
            "simulator_enabled": False,
            "api_port": 5000
        }

        # Configuración por defecto multi-PLC
        self.default_multi_config = {
            "api_config": {
                "port": 5000,
                "debug": False,
                "allowed_origins": "http://localhost,http://127.0.0.1,http://192.168.1.0/24,http://localhost:3000"
            },
            "plc_machines": [],
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "connection_log_enabled": True
            }
        }

        # Crear carpeta de backups si no existe
        os.makedirs(self.backup_folder, exist_ok=True)

    def load_single_config(self) -> Dict[str, Any]:
        """
        Carga la configuración single-PLC.

        Returns:
            Diccionario con la configuración single-PLC
        """
        if os.path.exists(self.single_config_file):
            try:
                with open(self.single_config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.logger.info(
                        "Configuración single-PLC cargada correctamente")
                    return config
            except Exception as e:
                self.logger.error(
                    f"Error cargando configuración single-PLC: {e}")
                return self.default_single_config.copy()
        return self.default_single_config.copy()

    def save_single_config(self, config: Dict[str, Any]) -> bool:
        """
        Guarda la configuración single-PLC.

        Args:
            config: Diccionario con la configuración

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear backup antes de guardar
            self._create_backup(self.single_config_file)

            with open(self.single_config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.logger.info("Configuración single-PLC guardada correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando configuración single-PLC: {e}")
            return False

    def load_multi_config(self) -> Optional[Dict[str, Any]]:
        """
        Carga la configuración multi-PLC.

        Returns:
            Diccionario con la configuración multi-PLC o None si no existe
        """
        if os.path.exists(self.multi_config_file):
            try:
                with open(self.multi_config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.logger.info(
                        f"Configuración multi-PLC cargada: {len(config.get('plc_machines', []))} máquinas")
                    return config
            except Exception as e:
                self.logger.error(
                    f"Error cargando configuración multi-PLC: {e}")
                return None
        return None

    def save_multi_config(self, config: Dict[str, Any]) -> bool:
        """
        Guarda la configuración multi-PLC.

        Args:
            config: Diccionario con la configuración multi-PLC

        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            # Crear backup antes de guardar
            self._create_backup(self.multi_config_file)

            with open(self.multi_config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            machines_count = len(config.get('plc_machines', []))
            self.logger.info(
                f"Configuración multi-PLC guardada: {machines_count} máquinas")
            return True
        except Exception as e:
            self.logger.error(f"Error guardando configuración multi-PLC: {e}")
            return False

    def get_machines_list(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de máquinas configuradas.

        Returns:
            Lista de máquinas o lista vacía si no hay configuración multi-PLC
        """
        multi_config = self.load_multi_config()
        if multi_config:
            return multi_config.get('plc_machines', [])
        return []

    def add_machine(self, machine_data: Dict[str, Any]) -> bool:
        """
        Añade una nueva máquina a la configuración.

        Args:
            machine_data: Datos de la máquina
                         {"id": "machine_x", "name": "Nombre", "ip": "192.168.1.x", "port": 3200, "simulator": False}

        Returns:
            True si se añadió correctamente, False en caso contrario
        """
        try:
            # Cargar configuración existente o crear nueva
            multi_config = self.load_multi_config()
            if not multi_config:
                multi_config = self.default_multi_config.copy()

            # Verificar que el ID no exista
            existing_ids = [m["id"] for m in multi_config["plc_machines"]]
            if machine_data["id"] in existing_ids:
                self.logger.error(
                    f"Ya existe una máquina con ID: {machine_data['id']}")
                return False

            # Validar datos requeridos
            required_fields = ["id", "name", "ip", "port"]
            for field in required_fields:
                if field not in machine_data:
                    self.logger.error(f"Campo requerido faltante: {field}")
                    return False

            # Añadir valores por defecto si no están presentes
            machine_data.setdefault("simulator", False)
            machine_data.setdefault(
                "description", f"Máquina {machine_data['name']}")

            # Añadir la máquina
            multi_config["plc_machines"].append(machine_data)

            # Guardar configuración
            return self.save_multi_config(multi_config)

        except Exception as e:
            self.logger.error(f"Error añadiendo máquina: {e}")
            return False

    def update_machine(self, machine_id: str, machine_data: Dict[str, Any]) -> bool:
        """
        Actualiza una máquina existente.

        Args:
            machine_id: ID de la máquina a actualizar
            machine_data: Nuevos datos de la máquina

        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            multi_config = self.load_multi_config()
            if not multi_config:
                self.logger.error("No existe configuración multi-PLC")
                return False

            # Buscar la máquina
            machine_found = False
            for i, machine in enumerate(multi_config["plc_machines"]):
                if machine["id"] == machine_id:
                    # Preservar el ID original
                    machine_data["id"] = machine_id
                    multi_config["plc_machines"][i] = machine_data
                    machine_found = True
                    break

            if not machine_found:
                self.logger.error(f"Máquina con ID {machine_id} no encontrada")
                return False

            return self.save_multi_config(multi_config)

        except Exception as e:
            self.logger.error(f"Error actualizando máquina: {e}")
            return False

    def remove_machine(self, machine_id: str) -> bool:
        """
        Elimina una máquina de la configuración.

        Args:
            machine_id: ID de la máquina a eliminar

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            multi_config = self.load_multi_config()
            if not multi_config:
                self.logger.error("No existe configuración multi-PLC")
                return False

            # Filtrar la máquina a eliminar
            original_count = len(multi_config["plc_machines"])
            multi_config["plc_machines"] = [
                m for m in multi_config["plc_machines"] if m["id"] != machine_id
            ]

            if len(multi_config["plc_machines"]) == original_count:
                self.logger.error(f"Máquina con ID {machine_id} no encontrada")
                return False

            return self.save_multi_config(multi_config)

        except Exception as e:
            self.logger.error(f"Error eliminando máquina: {e}")
            return False

    def get_machine_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una máquina específica por su ID.

        Args:
            machine_id: ID de la máquina

        Returns:
            Datos de la máquina o None si no se encuentra
        """
        machines = self.get_machines_list()
        for machine in machines:
            if machine["id"] == machine_id:
                return machine
        return None

    def is_multi_plc_enabled(self) -> bool:
        """
        Verifica si el sistema multi-PLC está habilitado.

        Returns:
            True si hay configuración multi-PLC con máquinas, False en caso contrario
        """
        multi_config = self.load_multi_config()
        return multi_config is not None and len(multi_config.get('plc_machines', [])) > 0

    def switch_to_single_plc(self) -> bool:
        """
        Cambia al modo single-PLC deshabilitando la configuración multi-PLC.

        Returns:
            True si se cambió correctamente
        """
        try:
            if os.path.exists(self.multi_config_file):
                # Crear backup antes de eliminar
                backup_name = f"multi_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = os.path.join(self.backup_folder, backup_name)
                shutil.copy2(self.multi_config_file, backup_path)

                # Eliminar archivo multi-PLC
                os.remove(self.multi_config_file)
                self.logger.info("Sistema cambiado a modo single-PLC")

            return True
        except Exception as e:
            self.logger.error(f"Error cambiando a single-PLC: {e}")
            return False

    def _create_backup(self, config_file: str) -> None:
        """
        Crea un backup del archivo de configuración.

        Args:
            config_file: Ruta del archivo a respaldar
        """
        if os.path.exists(config_file):
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{os.path.splitext(os.path.basename(config_file))[0]}_backup_{timestamp}.json"
                backup_path = os.path.join(self.backup_folder, backup_name)
                shutil.copy2(config_file, backup_path)

                # Mantener solo los últimos 10 backups
                self._cleanup_old_backups()

            except Exception as e:
                self.logger.warning(f"No se pudo crear backup: {e}")

    def _cleanup_old_backups(self) -> None:
        """Elimina backups antiguos, manteniendo solo los últimos 10."""
        try:
            backup_files = [f for f in os.listdir(
                self.backup_folder) if f.endswith('.json')]
            backup_files.sort(key=lambda x: os.path.getctime(
                os.path.join(self.backup_folder, x)))

            # Eliminar archivos antiguos si hay más de 10
            while len(backup_files) > 10:
                old_file = backup_files.pop(0)
                os.remove(os.path.join(self.backup_folder, old_file))

        except Exception as e:
            self.logger.warning(f"Error limpiando backups: {e}")

    def validate_machine_data(self, machine_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Valida los datos de una máquina.

        Args:
            machine_data: Datos de la máquina a validar

        Returns:
            Tupla (es_válido, mensaje_error)
        """
        try:
            # Validar campos requeridos
            required_fields = ["id", "name", "ip", "port"]
            for field in required_fields:
                if field not in machine_data or not machine_data[field]:
                    return False, f"Campo requerido faltante o vacío: {field}"

            # Validar formato del ID
            machine_id = machine_data["id"].strip()
            if not machine_id.replace("_", "").replace("-", "").isalnum():
                return False, "El ID debe contener solo letras, números, guiones y guiones bajos"

            # Validar que el nombre no esté vacío
            if not machine_data["name"].strip():
                return False, "El nombre no puede estar vacío"

            # Validar IP
            ip_parts = machine_data["ip"].split(".")
            if len(ip_parts) != 4:
                return False, "Formato de IP inválido"

            for part in ip_parts:
                if not part.isdigit() or not (0 <= int(part) <= 255):
                    return False, "Formato de IP inválido"

            # Validar puerto
            try:
                port = int(machine_data["port"])
                if not (1 <= port <= 65535):
                    return False, "El puerto debe estar entre 1 y 65535"
            except ValueError:
                return False, "El puerto debe ser un número válido"

            return True, ""

        except Exception as e:
            return False, f"Error validando datos: {str(e)}"
