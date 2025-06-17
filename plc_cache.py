import threading
from filelock import FileLock

# Lock global en memoria (intra-proceso)
plc_status_cache = {'status': None, 'timestamp': 0}
plc_access_lock = threading.Lock()

# Lock interproceso (file lock)
# Bloquea acceso entre procesos
plc_interprocess_lock = FileLock("plc_access.lock")
