# Bob (ESP32)

Sisi **Bob**: TCP server + *corrector* pada protokol SKG. Berjalan di ESP32 sebagai sketch
Arduino C++. Dataset RSSI di-embed (`synced_bob.h`) → tidak perlu filesystem/SD.

## Syarat
- Arduino IDE **atau** `arduino-cli`.
- Board package **esp32** by Espressif.
- ESP32 klasik (mis. ESP32-D0WD / Dev Module), WiFi 2.4 GHz.

## File
| File | Fungsi |
|---|---|
| `bob_esp32/bob_esp32.ino` | sketch utama (WiFi, TCP server, alur protokol) |
| `bob_esp32/skg.h` | 4 langkah SKG di C++ (SHA3, quantisasi, Cascade, kunci) |
| `bob_esp32/synced_bob.h` | dataset RSSI Bob (1164 sampel, embedded sebagai C array) |
| `synced_bob.csv` | dataset RSSI Bob mentah (sumber, mudah dibaca) |
| `gen_header.py` | regenerasi `synced_bob.h` dari `synced_bob.csv` |

> **Catatan RSSI:** sistem ini berbasis RSSI. `synced_bob.csv` = data mentah; `synced_bob.h` =
> data sama yang di-embed ke firmware (ESP32 Arduino tak baca file flash dengan mudah).
> Ganti dataset: ubah `synced_bob.csv` lalu jalankan `python gen_header.py`.

## Konfigurasi (di `bob_esp32.ino`)
```cpp
const char* WIFI_SSID = "NAMA_HOTSPOT";
const char* WIFI_PASS = "PASSWORD_HOTSPOT";
const int   PORT      = 6000;
const double ALPHA    = 1.0;   // HARUS sama dengan alice.py
```

## Cara A — Arduino IDE
1. Tambah Boards Manager URL (Preferences):
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
2. Boards Manager → install **esp32**.
3. Buka `bob_esp32/bob_esp32.ino`, isi WiFi.
4. *Tools → Board* = **ESP32 Dev Module**, pilih Port.
5. **Upload**, lalu buka **Serial Monitor** (115200) → catat `IP ESP32`.

## Cara B — arduino-cli
```
arduino-cli core install esp32:esp32
arduino-cli compile --fqbn esp32:esp32:esp32 bob_esp32
arduino-cli upload  --fqbn esp32:esp32:esp32 -p COM_ESP32 bob_esp32
arduino-cli monitor -p COM_ESP32 -c baudrate=115200
```

## Output benar (Serial Monitor)
```
WiFi OK, IP ESP32 = 192.168.x.y
Bob menunggu Alice connect di port 6000...
Alice terhubung.
Sifting: posisi bersama = 123
Rekonsiliasi selesai, query parity = 88
STATUS: MATCH
Kunci Bob: 4c032a3015f75237aafbf66bd279aaaab4fa7b73d64291ec15aa31705e067ed8
```

## Catatan
- Cetak titik (`.....`) terus = WiFi gagal: cek SSID/pass, pastikan 2.4 GHz.
- Ulang demo: tekan tombol **EN/RST** di ESP32, lalu jalankan `alice.py` lagi.
- Mau ganti dataset? Regenerasi `synced_bob.h` dari CSV (array `RSSI_BOB[]`, `N_BOB`).
