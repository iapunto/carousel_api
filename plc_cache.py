import json
import os
import threading
import time
from filelock import FileLock

# Lock global en memoria (intra-proceso)
plc_status_cache = {'status': None, 'timestamp': 0}
plc_access_lock = threading.Lock()

# Lock interproceso (file lock)
# Bloquea acceso entre procesos
plc_interprocess_lock = FileLock("plc_access.lock")

# ---------------------------------------------------------------
# Caché de estado del PLC compartida entre procesos (archivo JSON).
#
# Un único proceso (el WebSocket server) consulta el PLC en segundo
# plano y escribe aquí el resultado. Los demás procesos (API Flask,
# GUI vía HTTP) leen esta caché en lugar de abrir otra conexión TCP
# al PLC — así el PLC recibe UNA consulta por intervalo sin importar
# cuántos clientes pregunten.
# ---------------------------------------------------------------

STATUS_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "plc_status_cache.json")


def _read_cache_file() -> dict:
    try:
        with open(STATUS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_machine_status(machine_id: str, data: dict):
    """Guarda el estado de una máquina en la caché compartida.

    Formato: {machine_id: {"data": <status dict>, "ts": <epoch>}}
    """
    try:
        with plc_interprocess_lock:
            cache = _read_cache_file()
            cache[machine_id] = {"data": data, "ts": time.time()}
            tmp = STATUS_CACHE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f)
            os.replace(tmp, STATUS_CACHE_FILE)
    except Exception:
        # La caché es best-effort: nunca debe tumbar al poller ni a la API
        pass


def read_cached_status(machine_id: str = None, max_age: float = None):
    """Lee la caché compartida.

    Args:
        machine_id: Si se da, retorna solo la entrada de esa máquina
                    (o None si no existe / expiró).
        max_age: Antigüedad máxima en segundos. Entradas más viejas
                 se consideran expiradas.

    Returns:
        En modo multi-máquina (machine_id=None): {machine_id: data}
        En modo individual: el dict 'data' de la máquina o None.
    """
    now = time.time()
    cache = _read_cache_file()

    if machine_id is None:
        result = {}
        for mid, entry in cache.items():
            if max_age is None or (now - entry.get("ts", 0)) <= max_age:
                result[mid] = entry.get("data")
        return result

    entry = cache.get(machine_id)
    if not entry:
        return None
    if max_age is not None and (now - entry.get("ts", 0)) > max_age:
        return None
    return entry.get("data")


# ---------------------------------------------------------------
# Última posición COMANDADA por nosotros (tracking propio).
#
# El byte de posición del PLC no es confiable (observado: siempre
# devuelve 0 aunque la máquina esté en otro cangilón). La única fuente
# de verdad disponible en software es "a dónde la mandamos nosotros".
# Se persiste aquí para sobrevivir reinicios de la API.
# ---------------------------------------------------------------

_LAST_POS_KEY_SUFFIX = "__last_commanded_position"


def write_last_position(machine_id: str, position: int):
    """Registra la última posición comandada (1-indexada)."""
    try:
        with plc_interprocess_lock:
            cache = _read_cache_file()
            cache[machine_id + _LAST_POS_KEY_SUFFIX] = {
                "data": position, "ts": time.time()}
            tmp = STATUS_CACHE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(cache, f)
            os.replace(tmp, STATUS_CACHE_FILE)
    except Exception:
        pass


def read_last_position(machine_id: str):
    """Lee la última posición comandada (1-indexada) o None."""
    entry = _read_cache_file().get(machine_id + _LAST_POS_KEY_SUFFIX)
    return entry.get("data") if entry else None
