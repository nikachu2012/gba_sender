import time

import serial


def exchange32(handler: serial.Serial, data: int) -> int:
    # u32相当のデータをリトルエンディアンのバイト列に変換
    buf = data.to_bytes(4, byteorder="little")

    # 送信
    handler.write(buf)

    # 受信
    recv_buf = handler.read(4)

    return int.from_bytes(recv_buf, byteorder="little")


def exchange16(handler: serial.Serial, data: int) -> int:
    # 32ビット幅にマスクして送信し、上位16ビットを返す
    r = exchange32(handler, data & 0xFFFFFFFF)
    return (r >> 16) & 0xFFFF


def send(handler: serial.Serial, f: bytes):
    print("Waiting connection...")

    xy = 0
    count = 0
    while True:
        r = exchange16(handler, 0x6200)

        if (r & 0xFFF0) == 0x7200:
            xy = r & 0xF
            count += 1

            # 15回繰り返す
            if count >= 15:
                break
            else:
                continue

        # retry wait
        time.sleep(1.0 / 16.0)

    r = exchange16(handler, 0x6100 | xy)
    assert (r & 0xFFF0) == 0x7200, "Assertion failed: 0x6100 step"

    # transfer header
    print("Sending Header...")

    for i in range(0, 0xC0, 2):
        data_16 = f[i] | (f[i + 1] << 8)
        r = exchange16(handler, data_16)
        print(f"0x{r:04x}")

        assert (r >> 8) == (0xC0 - i) // 2
        assert (r & 0xFF) == xy

    # complete transfer header
    r = exchange16(handler, 0x6200)
    assert (r & 0xF) == xy

    # exchange master slave info
    r = exchange16(handler, 0x6200 | xy)
    assert r == (0x7200 | xy)
    assert (r & 0xF) == xy

    # send palette data
    # recv client data
    pp = 0xD1

    cc = 0
    while True:
        r = exchange16(handler, 0x6300 | pp)

        if (r & 0xFF00) == 0x7300:
            cc = r & 0xFF
            break

    # send handshake data
    hh = (cc + 0x11 + 0xFF + 0xFF) & 0xFF
    r = exchange16(handler, 0x6400 | hh)
    assert (r & 0xFF00) == 0x7300

    # wait 1/16s
    time.sleep(1.0 / 16.0)

    # PROCESS SWI 25h

    # get file size
    file_len = len(f)
    size_calc = (((file_len - 0xC0) // 4) - 0x34) & 0xFFFF
    r = exchange16(handler, size_calc)
    assert (r & 0xFF00) == 0x7300
    rr = r & 0xFF

    # encrypt data
    print("Sending Data...")

    c = 0xC387
    x = 0xC37B
    k = 0x43202F2F
    m = (0xFFFF0000 | (cc << 8) | pp) & 0xFFFFFFFF
    ff = (0xFFFF0000 | (rr << 8) | hh) & 0xFFFFFFFF

    for ptr in range(0xC0, file_len, 4):
        data = f[ptr] | (f[ptr + 1] << 8) | (f[ptr + 2] << 16) | (f[ptr + 3] << 24)
        c = c ^ data
        for _ in range(32):
            carry = (c & 0b1) == 1
            c = c >> 1

            if carry:
                c = c ^ x

        # Rustの `wrapping_mul` 相当の処理 (32ビット幅でオーバーフローさせる)
        m = ((m * 0x6F646573) + 1) & 0xFFFFFFFF

        # ptr を u32 として計算
        ptr_u32 = ptr & 0xFFFFFFFF
        sub_val = (0xFE000000 - ptr_u32) & 0xFFFFFFFF
        send_data = data ^ sub_val ^ m ^ k

        r = exchange32(handler, send_data)
        # print(f"0x{r:08x}")

        assert (r >> 16) == (ptr & 0xFFFF)

    # checksum update
    c = c ^ ff
    for _ in range(32):
        carry = (c & 0b1) == 1
        c = c >> 1

        if carry:
            c = c ^ x

    r = exchange16(handler, 0x0065)
    # print(f"len=0x{file_len:04x}")
    # print(f"0x{r:04x}")
    assert r == (file_len & 0xFFFF)

    # wait send checksum
    while True:
        r = exchange16(handler, 0x0065)
        # print(f"0x{r:04x}")

        if (r & 0xFFFF) == 0x0075:
            break

    r = exchange16(handler, 0x0066)
    assert (r & 0xFFFF) == 0x0075

    r = exchange16(handler, c & 0xFFFF)
    assert (r & 0xFFFF) == (c & 0xFFFF)

    print("Send completed!")
