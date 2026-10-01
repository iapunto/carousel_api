"""Cliente Modbus TCP mínimo para PLC Delta AS — lectura de posición real.

Contexto: el protocolo propietario :3200 devuelve el byte de posición
siempre en 0 (bug del lado del PLC/firmware). La posición física real
vive en el registro D0 del Delta AS218P, accesible por Modbus TCP :502:

- D0 (addr 0): posición FÍSICA actual, 0-indexada — actualiza al llegar
- D2/D22 (addr 2/22): posición OBJETIVO/comandada — actualiza al recibir
  el comando (puede diferir de D0 si el movimiento no se ejecutó)

Direcciones configurables por variables de entorno por si el programa
del PLC del cliente las mapea distinto.
"""
import os
import socket
import struct
import time

MODBUS_PORT = int(os.getenv("PLC_MODBUS_PORT", "502"))
# Registros (dirección PDU). D<n> en la AS mapea directo a addr <n> en
# este rango bajo del banco de registros holding.
POS_ADDR = int(os.getenv("PLC_MODBUS_POS_ADDR", "0"))
TARGET_ADDR = int(os.getenv("PLC_MODBUS_TARGET_ADDR", "2"))

_tid = [0]
_tid_lock = __import__("threading").Lock()

# Circuit breaker por IP: con el PLC fuera de red cada lectura costaría
# ~3s de timeout por socket; tras un fallo se abre el circuito unos
# segundos y las lecturas devuelven None al instante.
_offline_until = {}
OFFLINE_WINDOW = float(os.getenv("PLC_MODBUS_OFFLINE_SECONDS", "15"))


def read_registers(ip: str, start: int, count: int,
                   timeout: float = 3.0):
    """Lee 'count' holding registers (func 03) desde 'start'.

    Returns: lista de enteros, o None si falla la comunicación.
    """
    if time.time() < _offline_until.get(ip, 0):
        return None
    with _tid_lock:
        _tid[0] += 1
        tid = _tid[0]
    pdu = struct.pack(">BHH", 3, start, count)
    packet = struct.pack(">HHHB", tid, 0, len(pdu) + 1, 1) + pdu
    try:
        with socket.create_connection((ip, MODBUS_PORT), timeout=timeout) as s:
            s.sendall(packet)
            hdr = s.recv(7)
            if len(hdr) < 7:
                raise OSError("respuesta Modbus incompleta")
            _, _, length, _ = struct.unpack(">HHHB", hdr)
            body = b""
            while len(body) < length - 1:
                chunk = s.recv(length - 1 - len(body))
                if not chunk:
                    raise OSError("respuesta Modbus truncada")
                body += chunk
    except OSError:
        _offline_until[ip] = time.time() + OFFLINE_WINDOW
        return None
    _offline_until.pop(ip, None)
    if not body or body[0] != 3:
        return None
    nbytes = body[1]
    return [
        struct.unpack(">H", body[2 + i:4 + i])[0]
        for i in range(0, nbytes, 2)
    ]


def read_real_position(ip: str, timeout: float = 3.0):
    """Posición física real (0-indexada) leída de D0. None si falla."""
    vals = read_registers(ip, POS_ADDR, 1, timeout=timeout)
    return vals[0] if vals else None


def read_target_position(ip: str, timeout: float = 3.0):
    """Posición objetivo/comandada (0-indexada) leída de D2."""
    vals = read_registers(ip, TARGET_ADDR, 1, timeout=timeout)
    return vals[0] if vals else None
