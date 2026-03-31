import argparse
import sys
import time

import serial

from util import exchange32, send

SERIAL_SPEED = 9600
DUMP_BIOS = 3


def open_port(port_name: str) -> serial.Serial:
    try:
        return serial.Serial(
            port=port_name,
            baudrate=SERIAL_SPEED,
            timeout=0.01,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
        )
    except Exception as e:
        print(f'Failed to open "{port_name}". Error: {e}', file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="dump GBA BIOS via multiboot")
    parser.add_argument("output", help="output file (position argument)")
    parser.add_argument("port", help="serial port (position argument)")
    args = parser.parse_args()

    with open("gba_sender_mb.gba", "rb") as fh:
        f = bytearray(fh.read())

    while len(f) % 16 != 0:
        f.append(0)

    if len(f) > 0x40000:
        raise SystemExit("file too large!")

    port = open_port(args.port)

    send(port, bytes(f))

    time.sleep(1)

    r = exchange32(port, DUMP_BIOS)
    assert r == 0x10101010

    BIOS_SIZE = 0x4000
    bios = bytearray(BIOS_SIZE)

    for i in range(0, BIOS_SIZE, 4):
        r = exchange32(port, i & 0xFFFFFFFF)
        bios[i] = r & 0xFF
        bios[i + 1] = (r >> 8) & 0xFF
        bios[i + 2] = (r >> 16) & 0xFF
        bios[i + 3] = (r >> 24) & 0xFF

    with open(args.output, "wb") as ofh:
        ofh.write(bios)

    print("BIOS dump completed.")


if __name__ == "__main__":
    main()
