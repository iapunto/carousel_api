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
import logging
import eventlet
import eventlet.green.threading as threading
from flask_socketio import SocketIO
import copy

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


def monitor_plc_status(socketio, plc, interval=1.0):
    """
    Hilo que monitorea el estado del PLC y emite eventos WebSocket solo si hay cambios.
    Args:
        socketio: Instancia de SocketIO.
        plc: Instancia de PLC o simulador.
        interval: Intervalo de consulta en segundos.
    """
    last_status = None
    while True:
        try:
            status = plc.get_current_status()
            if last_status is None or status != last_status:
                socketio.emit('plc_status', status)
                last_status = copy.deepcopy(status)
        except Exception as e:
            socketio.emit('plc_status_error', {'error': str(e)})
        eventlet.sleep(interval)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("carousel_api.log"),
            logging.StreamHandler()
        ]
    )
    # Cargar configuración
    config = load_config()

    # Crear instancia del PLC
    plc = create_plc_instance(config)

    # Crear y configurar API Flask
    flask_app = create_app(plc)
    socketio = SocketIO(flask_app, cors_allowed_origins="*",
                        async_mode="eventlet")

    # Iniciar hilo de monitoreo de PLC antes de socketio.run
    eventlet.spawn_n(monitor_plc_status, socketio, plc, 1.0)
    # Iniciar API y WebSocket en hilo principal
    socketio.run(flask_app, host="0.0.0.0", port=config.get("api_port", 5000))

    # Iniciar interfaz gráfica
    root = tk.Tk()
    app_gui = MainWindow(root, plc, config)
    root.mainloop()
