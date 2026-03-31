#include <Arduino.h>

const int SC_PIN = 2;  // SCK
const int SI_PIN = 3;  // MOSI TX
const int SO_PIN = 4;  // MISO RX

void setup() {
  Serial.begin(9600);

  pinMode(SC_PIN, OUTPUT);
  pinMode(SI_PIN, OUTPUT);
  pinMode(SO_PIN, INPUT);

  digitalWrite(SC_PIN, HIGH);
  digitalWrite(SI_PIN, HIGH);
  // digitalWrite(SO_PIN, HIGH);
}

uint32_t exchange(uint32_t data) {
  uint32_t input = 0;

  // 最上位ビットから送信する
  for (int i = 31; i >= 0; i--) {
    // HIGH->LOWの時に送信
    digitalWrite(SC_PIN, LOW);
    digitalWrite(SI_PIN, ((data >> i) & 0b1) ? HIGH : LOW);

    delayMicroseconds(4);

    // LOW->HIGHの時に受信
    digitalWrite(SC_PIN, HIGH);
    input |= (digitalRead(SO_PIN) == HIGH ? 1 : 0) << i;

    delayMicroseconds(4);
  }

  // 出力ピンをHIGHに戻す
  digitalWrite(SI_PIN, HIGH);

  return input;
}

void loop() {
  uint8_t buf[4];
  uint32_t data;

  if (Serial.available() >= 4) {
    Serial.readBytes(buf, 4);

    data = buf[0] | buf[1] << 8 | buf[2] << 16 | buf[3] << 24;

    data = exchange(data);

    buf[0] = data & 0xff;
    buf[1] = data >> 8 & 0xff;
    buf[2] = data >> 16 & 0xff;
    buf[3] = data >> 24 & 0xff;

    Serial.write(buf, 4);
  }
}
