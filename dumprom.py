import argparse
import sys
import time

import serial

from util import exchange32, send

SERIAL_SPEED = 9600
DUMP_ROM = 1


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
    parser = argparse.ArgumentParser(description="dumprom from GBA via multiboot")
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

    r = exchange32(port, DUMP_ROM)
    print(f"result: 0x{r:08x}")

    time.sleep(1)

    gamesize = exchange32(port, 0xFFFFFFFF)
    print(f"Gamesize: {gamesize // 1024}KiB")

    data = bytearray(gamesize)

    for i in range(0, gamesize, 4):
        r = exchange32(port, (i // 4) & 0xFFFFFFFF)
        data[i] = r & 0xFF
        data[i + 1] = (r >> 8) & 0xFF
        data[i + 2] = (r >> 16) & 0xFF
        data[i + 3] = (r >> 24) & 0xFF

        if (i % 1024) == 0:
            print(f"{i // 1024}KiB / {gamesize // 1024}KiB")

    with open(args.output, "wb") as ofh:
        ofh.write(data)


if __name__ == "__main__":
    main()
