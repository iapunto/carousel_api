import threading

plc_status_cache = {'status': None, 'timestamp': 0}
plc_access_lock = threading.Lock()
