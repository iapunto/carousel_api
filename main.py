"""
Aplicación de escritorio para control de carrusel industrial
Autor: Industrias Pico S.A.S
Fecha: 2024-09-27
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from api import create_app  # Importa la API [[3]]
from models.plc import PLC  # Importa PLC real
from gui.main_gui import MainWindow  # Interfaz gráfica

# Configuración persistente [[1]]
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "ip": "192.168.1.100",
    "port": 3200,
    "simulator_enabled": False
}


def load_config():
    """Carga la configuración desde archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Punto de revisión [[6]]
            print(f"Configuración cargada: {config}")
            return config
    return DEFAULT_CONFIG


config = load_config()
plc_mode = "Simulador" if config.get(
    "simulator_enabled", False) else "PLC Real"
# Punto de revisión [[6]]
print(
    f"Iniciando en modo: {plc_mode}, IP: {config['ip']}, Puerto: {config['port']}")

if config.get("simulator_enabled", False):
    from models.plc_simulator import PLCSimulator as PLC
else:
    from models.plc import PLC

plc = PLC(config["ip"], config["port"])


def create_plc_instance(config):
    """Crea instancia del PLC según modo [[6]]"""
    if config.get("simulator_enabled", False):
        from models.plc_simulator import PLCSimulator
        return PLCSimulator(config["ip"], config["port"])
    else:
        return PLC(config["ip"], config["port"])


if __name__ == "__main__":
    # Cargar configuración
    config = load_config()

    # Crear instancia del PLC
    plc = create_plc_instance(config)

    # Crear y configurar API Flask
    flask_app = create_app(plc)

    # Iniciar API en hilo separado
    api_thread = threading.Thread(
        target=flask_app.run,
        # Usa el puerto configurado o 5001 por defecto
        kwargs={"host": "0.0.0.0", "port": config.get("api_port", 5000)},
        daemon=True
    )
    api_thread.start()

    # Iniciar interfaz gráfica
    root = tk.Tk()
    app_gui = MainWindow(root, plc, config)
    root.mainloop()
