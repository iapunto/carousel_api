"""Resincroniza el contador de posición del Delta AS218P vía Modbus TCP.

Uso: python modbus_resync.py <posicion_fisica_real_cangilon>
  Escribe posición-1 (0-indexada) en D2 y D22 (addr 2 y 22).
  Ejemplo: máquina físicamente en cangilón 3 -> python modbus_resync.py 3
"""
import socket
import struct
import sys

PLC = ("192.168.1.50", 502)
POSITION_ADDRS = [2, 22]  # D2 y D22 — confirmados como posición actual
_tid = [0]


def _mbap_pdu(pdu: bytes):
    _tid[0] += 1
    return struct.pack(">HHHB", _tid[0], 0, len(pdu) + 1, 1) + pdu


def _roundtrip(sock, packet: bytes) -> bytes:
    sock.sendall(packet)
    hdr = sock.recv(7)
    _, _, length, _ = struct.unpack(">HHHB", hdr)
    body = b""
    while len(body) < length - 1:
        body += sock.recv(length - 1 - len(body))
    return body


def write_register(sock, addr: int, value: int):
    pdu = struct.pack(">BHH", 6, addr, value)
    body = _roundtrip(sock, _mbap_pdu(pdu))
    if body[0] & 0x80:
        raise RuntimeError(f"Modbus exception {body[1]} en addr {addr}")
    return struct.unpack(">HH", body[3:7])


def read_register(sock, addr: int):
    pdu = struct.pack(">BHH", 3, addr, 1)
    body = _roundtrip(sock, _mbap_pdu(pdu))
    if body[0] & 0x80:
        raise RuntimeError(f"Modbus exception {body[1]} en addr {addr}")
    return struct.unpack(">H", body[2:4])[0]


def main():
    tray = int(sys.argv[1])
    idx = tray - 1  # 0-indexado
    with socket.create_connection(PLC, timeout=5) as s:
        for addr in POSITION_ADDRS:
            before = read_register(s, addr)
            write_register(s, addr, idx)
            after = read_register(s, addr)
            print(f"addr {addr}: {before} -> {after}")


if __name__ == "__main__":
    main()
