import argparse
import sys

import serial

from util import send

SERIAL_SPEED = 9600


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
    parser = argparse.ArgumentParser(description="send multiboot rom")
    parser.add_argument("filename", help="input file (position argument)")
    parser.add_argument("port", help="serial port (position argument)")
    args = parser.parse_args()

    with open(args.filename, "rb") as fh:
        f = bytearray(fh.read())

    # 16byte align padding
    while len(f) % 16 != 0:
        f.append(0)

    if len(f) > 0x40000:
        raise SystemExit("file too large!")

    port = open_port(args.port)

    send(port, bytes(f))


if __name__ == "__main__":
    main()
