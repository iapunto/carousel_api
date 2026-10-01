"""Barrido de registros Delta AS218P vía HTTP P-read.

Uso: python scan_delta_regs.py [start] [count] [chunk]
Lectura: GET http://192.168.1.50/P{addr}_{len}.xml
Delta: D0 = dirección 4096 (0x1000)
"""
import re
import sys
import urllib.request

BASE = "http://192.168.1.50"


def read_block(addr: int, length: int):
    url = f"{BASE}/P{addr}_{length}.xml"
    with urllib.request.urlopen(url, timeout=5) as r:
        xml = r.read().decode()
    return [int(v, 16) for v in re.findall(r"<V>0x([0-9A-Fa-f]+)</V>", xml)]


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 4096  # D0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 512   # D0-D511
    chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    nonzero = []
    for off in range(0, count, chunk):
        addr = start + off
        n = min(chunk, count - off)
        try:
            vals = read_block(addr, n)
        except Exception as e:
            print(f"addr {addr}: ERROR {e}")
            continue
        for i, v in enumerate(vals):
            if v != 0:
                nonzero.append((addr + i, v, addr + i - 4096 if addr + i >= 4096 else None))

    print(f"Registros no-cero en rango {start}..{start + count - 1}:")
    for addr, val, dreg in nonzero:
        d = f" (D{dreg})" if dreg is not None else ""
        print(f"  addr={addr}{d}  hex=0x{val:04X}  dec={val}")


if __name__ == "__main__":
    main()
