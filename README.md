# GBA Sender

ゲームボーイアドバンス（GBA）にPCからマルチブート用のROMを送信するためのアプリケーションです。

ついでにGBAからROM、BIOSのダンプもすることができます。

## 使い方

### まず最初に

`sender/gba_sender.ino`にあるArduinoファイルを、Arduino Coreに対応したマイコンボードに書き込んでください。

GBAのロジックレベルが3.3Vなので3.3V動作のマイコンをお勧めします。Raspberry Pi Picoが安くておすすめです。

このマイコンは、以下の図のように動作します。

```mermaid
flowchart LR
 PC -- シリアル通信 --> マイコン -- SPI風通信--> GBA
```

マイコンとGBAは、初期状態では以下のように接続してください。

この接続端子は、`sender/gba_sender.ino`で変更することができます。

ケーブル側のピン配置は以下のようになります。

```
   +-+
/--+ +--\
| 1 3 5 |
| 2 4 6 |
+-------+
```

| GBA側   | マイコン側 |
| ------- | ---------- |
| SC (5)  | GPIO2      |
| SI (3)  | GPIO3      |
| SO (2)  | GPIO4      |
| GND (6) | GND        |

### Pythonの準備
pyserialが必要です。

```bash
pip install pyserial
```

### プログラムの送信

プログラムは、マルチブート用にコンパイルされている必要があります。

DevkitARMを使用している場合は、Makefileのターゲット名の最後に`_mb`をつけてコンパイルしてください。

```diff
-TARGET		:= $(notdir $(CURDIR))
+TARGET		:= $(notdir $(CURDIR))_mb
```

ROMの刺さっていない状態でGBAを起動します。
その後、以下のコマンドで送信することができます。

```bash
python sender.py <input.gba> <serial-port>
# 例
python sender.py template_mb.gba /dev/tty.usbserial-XXXXX
```

送信テスト用のプログラムを用意しています（`template_mb.gba`）。

> [!NOTE]
> シリアルポートはArduino IDEを用いて検索するのがおすすめです。


### ROMのダンプ

ダンプしたいROMをGBA本体に差した状態で起動し、起動画面でSTART+SELECTを同時押しします。

画面のNintendoロゴが消えた状態で、以下のコマンドを実行します。

> [!NOTE]
> ROMをダンプするには、実行しているディレクトリと同じディレクトリに、`gba_sender_mb.gba`が置かれている必要があります。
> クローンした状態のままなら気にする必要はありません。

```bash
python dumprom.py <output.gba> <serial-port>
# 例
python dumprom.py game_dump.gba /dev/tty.usbserial-XXXXX
```

8MiBのROM（ポケットモンスター サファイア）で30分ほどかかります。気長に待ってください。

途中でスリープ等が入ると止まったりすることがあります。スリープしないように設定することをお勧めします。

### BIOSのダンプ

ROMの刺さっていない状態でGBAを起動します。
その後、以下のコマンドでダンプすることができます。

> [!NOTE]
> BIOSをダンプするには、実行しているディレクトリと同じディレクトリに、`gba_sender_mb.gba`が置かれている必要があります。
> クローンした状態のままなら気にする必要はありません。

```bash
python dumpbios.py <output.bin> <serial-port>
# 例
python dumpbios.py gba_bios.bin /dev/tty.usbserial-XXXXX
```

## スクリプト以外のビルド方法

`sender/`以下のファイルはArduino IDEでコンパイルを行ってください。

`gba/`以下のファイルはDevkitARMがインストールされた環境で`make`をしてください。

