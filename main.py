import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
from api import create_app  # Importa la API [[3]]
from models.plc import PLC  # Importa PLC real
from gui.main_gui import MainWindow  # Interfaz gráfica
import logging
import eventlet
import eventlet.green.threading as threading
from flask_socketio import SocketIO
import copy
import multiprocessing
import socket
import time
from plc_cache import plc_status_cache, plc_access_lock, plc_interprocess_lock
from commons.error_codes import PLC_CONN_ERROR, PLC_BUSY
from logging.handlers import RotatingFileHandler
import sys
import os
from commons.utils import debug_print
# Añade la ruta base del proyecto al sys.path para permitir imports de paquetes locales
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
os.environ["EVENTLET_NO_GREENDNS"] = "yes"
sys.modules["eventlet.support.greendns"] = None
site_packages = os.path.join(os.path.dirname(
    __file__), 'python_portable', 'site-packages')
if site_packages not in sys.path:
    sys.path.insert(0, site_packages)

"""
Aplicación de escritorio para control de carrusel industrial
Desarrollado: IA Punto Soluciones Tecnológicas 
Para: Industrias Pico S.A.S
Fecha: 2024-09-27
Actualizado: 2025-06-14
"""

# Configuración persistente [[1]]
CONFIG_FILE = "config.json"
MULTI_PLC_CONFIG_FILE = "config_multi_plc.json"
DEFAULT_CONFIG = {
    "ip": "192.168.1.50",
    "port": 3200,
    "simulator_enabled": False
}


def load_multi_plc_config():
    """Carga la configuración multi-PLC desde archivo JSON"""
    if os.path.exists(MULTI_PLC_CONFIG_FILE):
        with open(MULTI_PLC_CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            debug_print(
                f"Configuración multi-PLC cargada: {len(config.get('plc_machines', []))} máquinas")
            return config
    return None


def load_config():
    """Carga la configuración desde archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Punto de revisión [[6]]
            debug_print(f"Configuración cargada: {config}")
            return config
    return DEFAULT_CONFIG


config = load_config()
plc_mode = "Simulador" if config.get(
    "simulator_enabled", False) else "PLC Real"
# Punto de revisión [[6]]
debug_print(
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


def monitor_plc_status(socketio, plc, interval=5.0):
    """
    Hilo que monitorea el estado del PLC y emite eventos WebSocket solo si hay cambios.
    Ahora implementa reconexión automática y mantiene la conexión persistente.
    """
    import time as _time
    global plc_status_cache
    logger = logging.getLogger("monitor_plc_status")
    last_status = None
    consecutive_errors = 0
    max_errors = 3
    connected = False
    while True:
        try:
            logger.info("[MONITOR] Consultando estado del PLC...")
            # Bloqueo interproceso antes del lock global
            interprocess_acquired = plc_interprocess_lock.acquire(timeout=2)
            if not interprocess_acquired:
                logger.warning(
                    "[MONITOR] PLC ocupado por otro proceso (interproceso)")
                socketio.emit('plc_status_error', {
                    'success': False,
                    'data': None,
                    'error': 'PLC ocupado por otro proceso, intente de nuevo en unos segundos',
                    'code': PLC_BUSY
                })
                _time.sleep(interval)
                continue
            acquired = plc_access_lock.acquire(timeout=2)
            if not acquired:
                plc_interprocess_lock.release()
                logger.warning(
                    "[MONITOR] No se pudo adquirir el lock para consultar el PLC (ocupado por comando)")
                socketio.emit('plc_status_error', {
                    'success': False,
                    'data': None,
                    'error': 'PLC ocupado, intente de nuevo en unos segundos',
                    'code': PLC_BUSY
                })
                _time.sleep(interval)
                continue
            try:
                if not connected:
                    socketio.emit('plc_reconnecting', {
                        'success': False,
                        'data': None,
                        'error': 'Intentando reconectar al PLC...',
                        'code': PLC_CONN_ERROR
                    })
                    logger.info("[MONITOR] Intentando reconectar al PLC...")
                    if not plc.connect():
                        logger.error("[MONITOR] Fallo al reconectar al PLC.")
                        socketio.emit('plc_status_error', {
                            'success': False,
                            'data': None,
                            'error': 'No se pudo reconectar al PLC',
                            'code': PLC_CONN_ERROR
                        })
                        raise RuntimeError("No se pudo reconectar al PLC")
                    connected = True
                    socketio.emit('plc_reconnected', {
                        'success': True,
                        'data': {'msg': 'Reconexión exitosa al PLC.'},
                        'error': None,
                        'code': None
                    })
                    logger.info("[MONITOR] Reconexión exitosa al PLC.")
                status = plc.get_current_status()
                logger.info(f"[MONITOR] Estado recibido: {status}")
            finally:
                plc_access_lock.release()
                plc_interprocess_lock.release()
            if 'error' in status:
                logger.error(
                    f"[MONITOR] Error reportado por PLC: {status['error']}")
                socketio.emit('plc_status_error', {
                    'success': False,
                    'data': None,
                    'error': status['error'],
                    'code': PLC_CONN_ERROR
                })
                raise RuntimeError(status['error'])
            if last_status is None or status != last_status:
                logger.info(f"[MONITOR] Emite evento 'plc_status': {status}")
                socketio.emit('plc_status', {
                    'success': True,
                    'data': status,
                    'error': None,
                    'code': None
                })
                last_status = status
                plc_status_cache.clear()
                plc_status_cache.update(status)
            consecutive_errors = 0
        except Exception as e:
            logger.error(f"[MONITOR] Error en monitor_plc_status: {e}")
            consecutive_errors += 1
            if consecutive_errors >= max_errors:
                connected = False
                logger.warning(
                    f"[MONITOR] Se alcanzó el máximo de errores consecutivos ({max_errors}), se intentará reconectar.")
            _time.sleep(interval)
        _time.sleep(interval)


def run_backend(config):
    from models.plc import PLC
    from models.plc_simulator import PLCSimulator
    from api import create_app
    from flask_socketio import SocketIO
    import eventlet
    import copy
    import logging

    def create_plc_instance(config):
        if config.get("simulator_enabled"):
            debug_print(
                f"Iniciando en modo: Simulador, IP: {config['ip']}, Puerto: {config['port']}")
            return PLCSimulator(config["ip"], config["port"])
        else:
            debug_print(
                f"Iniciando en modo: PLC real, IP: {config['ip']}, Puerto: {config['port']}")
            return PLC(config["ip"], config["port"])

    def monitor_plc_status(socketio, plc, interval=1.0):
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

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("carousel_api.log"),
            logging.StreamHandler()
        ]
    )

    # Verificar si hay configuración multi-PLC
    multi_plc_config = load_multi_plc_config()
    if multi_plc_config:
        debug_print("🔄 Iniciando en modo MULTI-PLC")
        # Importar PLCManager para modo multi-PLC
        from models.plc_manager import PLCManager
        plc_manager = PLCManager(multi_plc_config["plc_machines"])
        flask_app = create_app(plc_manager=plc_manager)
        debug_print(
            f"✅ Sistema multi-PLC iniciado con {len(multi_plc_config['plc_machines'])} máquinas")
    else:
        debug_print("🔄 Iniciando en modo SINGLE-PLC (fallback)")
        # Modo single-PLC original
        plc = create_plc_instance(config)
        flask_app = create_app(plc)
        eventlet.spawn_n(monitor_plc_status, socketio, plc, 1.0)
        debug_print("✅ Sistema single-PLC iniciado")

    socketio = SocketIO(flask_app, cors_allowed_origins="*",
                        async_mode="eventlet")
    api_port = multi_plc_config.get("api_config", {}).get(
        "port", 5000) if multi_plc_config else config.get("api_port", 5000)
    socketio.run(flask_app, host="0.0.0.0", port=api_port)


if __name__ == "__main__":
    config = load_config()
    backend_process = multiprocessing.Process(
        target=run_backend, args=(config,), daemon=True)
    backend_process.start()

    # Esperar a que el backend esté listo antes de lanzar la GUI
    max_retries = 30
    backend_ready = False
    for i in range(max_retries):
        try:
            with socket.create_connection(("localhost", config.get("api_port", 5000)), timeout=1):
                backend_ready = True
                debug_print(
                    f"Backend disponible en puerto {config.get('api_port', 5000)}. Lanzando GUI...")
                break
        except (ConnectionRefusedError, OSError):
            debug_print(
                f"Esperando a que el backend esté listo... (intento {i+1}/{max_retries})")
            time.sleep(1)
    if not backend_ready:
        debug_print(
            f"ERROR: El backend no respondió en el puerto {config.get('api_port', 5000)} tras {max_retries} segundos. Abortando.")
        backend_process.terminate()
        sys.exit(1)

    # Iniciar GUI en el hilo principal
    root = tk.Tk()
    plc = None  # La GUI usará la API/WS, no acceso directo
    app_gui = MainWindow(root, plc, config)
    root.mainloop()
    backend_process.terminate()

# Configuración de logging global con rotación
file_log_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Vertical PIC', 'logs')
os.makedirs(file_log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(file_log_dir, "carousel_api.log")),
        logging.StreamHandler()
    ]
)
log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s')
