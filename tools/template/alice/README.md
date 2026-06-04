# Alice (Laptop)

Sisi **Alice**: client + *reference* pada protokol SKG. Dijalankan di laptop dengan Python.

## Syarat
- Python 3.8+ (tanpa library tambahan).
- Laptop tersambung WiFi/hotspot yang **sama** dengan ESP32.

## File
| File | Fungsi |
|---|---|
| `alice.py` | program utama (connect ke ESP32, sifting, jawab parity, verifikasi) |
| `skg_common.py` | 4 langkah SKG: quantisasi, sifting, Cascade, derive kunci |
| `sha3_256.py` | SHA3-256 (sama dengan `hashlib.sha3_256`) |
| `pcg32.py` | PRNG untuk permutasi Cascade |
| `net.py` | helper koneksi TCP (line-based) |
| `synced_alice.csv` | dataset RSSI Alice (1164 sampel) |

## Konfigurasi (di `alice.py`)
```python
PORT   = 6000
BOB_IP = "192.168.x.y"   # IP ESP32 dari Serial Monitor Arduino
ALPHA  = 1.0             # HARUS sama dengan bob_esp32.ino
CSV    = "synced_alice.csv"
```

## Jalankan
ESP32 harus sudah menyala & "menunggu Alice" dulu. Lalu:
```
cd alice
python alice.py
```

## Output benar
```
Alice: N=1164, kept(quantisasi)=300
Sifting: posisi bersama = 123
Kunci Alice : 4c032a3015f75237aafbf66bd279aaaab4fa7b73d64291ec15aa31705e067ed8
Kunci Bob   : 4c032a3015f75237aafbf66bd279aaaab4fa7b73d64291ec15aa31705e067ed8
Sama?       : YA
Status      : MATCH
```

## Catatan
- `Gagal connect` → cek `BOB_IP`, pastikan satu WiFi, ESP32 sudah listen.
- `RETRY` → kanal bising; naikkan `ALPHA` di **kedua** sisi (Alice & Bob) lalu ulang.
