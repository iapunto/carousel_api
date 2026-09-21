"""
Lanzador headless del backend Multi-PLC de carousel_api (puerto 5000).

Equivalente a `main.py::run_backend` pero sin GUI ni proceso padre:
pensado para ejecutarse como servicio/tarea programada en arranque de sesión.

Desarrollado: IA Punto Soluciones Tecnológicas
Para: Industrias Pico S.A.S
"""

import sys
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# Añade la ruta base del proyecto al sys.path para permitir imports de paquetes locales
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
os.chdir(base_dir)

os.environ["EVENTLET_NO_GREENDNS"] = "yes"
sys.modules["eventlet.support.greendns"] = None

MULTI_PLC_CONFIG_FILE = "config_multi_plc.json"
LOG_DIR = os.path.join(base_dir, "logs")


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            RotatingFileHandler(
                os.path.join(LOG_DIR, "carousel_service.log"),
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("carousel_service")

    if not os.path.exists(MULTI_PLC_CONFIG_FILE):
        logger.error("No existe %s", MULTI_PLC_CONFIG_FILE)
        sys.exit(1)

    with open(MULTI_PLC_CONFIG_FILE, encoding="utf-8") as f:
        multi_plc_config = json.load(f)

    machines = multi_plc_config.get("plc_machines", [])
    api_port = multi_plc_config.get("api_config", {}).get("port", 5000)

    import eventlet  # noqa: E402
    from flask_socketio import SocketIO  # noqa: E402
    from api import create_app  # noqa: E402
    from models.plc_manager import PLCManager  # noqa: E402

    plc_manager = PLCManager(machines)
    flask_app = create_app(plc_manager=plc_manager)
    logger.info("Multi-PLC iniciado con %d máquinas", len(machines))

    socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="eventlet")
    logger.info("API escuchando en 0.0.0.0:%d", api_port)
    socketio.run(flask_app, host="0.0.0.0", port=api_port)


if __name__ == "__main__":
    main()
