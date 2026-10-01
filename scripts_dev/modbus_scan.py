"""Cliente Modbus TCP crudo para Delta AS218P — lee registros sin pymodbus.

Uso: python modbus_scan.py <func> <start> <count>
  func: 3 = holding registers, 4 = input registers
  Delta AS: D0 = 0x1000 (4096), X=0x0400, Y=0x0500, M=0x0800, C=0x0E00
"""
import socket
import struct
import sys

PLC = ("192.168.1.50", 502)
_tid = [0]


def read_regs(func: int, start: int, count: int):
    _tid[0] += 1
    pdu = struct.pack(">BHH", func, start, count)
    mbap = struct.pack(">HHHB", _tid[0], 0, len(pdu) + 1, 1)
    with socket.create_connection(PLC, timeout=5) as s:
        s.sendall(mbap + pdu)
        hdr = s.recv(7)
        if len(hdr) < 7:
            raise RuntimeError(f"respuesta corta: {hdr!r}")
        _, _, length, _ = struct.unpack(">HHHB", hdr)
        body = b""
        while len(body) < length - 1:
            body += s.recv(length - 1 - len(body))
    if not body or body[0] != func:
        raise RuntimeError(f"respuesta inesperada: {body!r}")
    if body[0] & 0x80:
        raise RuntimeError(f"Modbus exception code {body[1]}")
    nbytes = body[1]
    vals = [struct.unpack(">H", body[2 + i:4 + i])[0] for i in range(0, nbytes, 2)]
    return vals


def main():
    func = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 4096
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    chunk = 60
    nonzero = []
    all_vals = {}
    for off in range(0, count, chunk):
        a = start + off
        n = min(chunk, count - off)
        try:
            vals = read_regs(func, a, n)
        except Exception as e:
            print(f"addr {a}: ERROR {e}")
            continue
        for i, v in enumerate(vals):
            all_vals[a + i] = v
            if v != 0:
                nonzero.append((a + i, v))
    print(f"no-cero (func {func}, {start}..{start + count - 1}): {len(nonzero)}")
    for a, v in nonzero:
        d = f" D{a - 4096}" if a >= 4096 else ""
        print(f"  addr={a}{d} hex=0x{v:04X} dec={v}")
    if len(sys.argv) > 4 and sys.argv[4] == "all":
        print("todos:", all_vals)


if __name__ == "__main__":
    main()
