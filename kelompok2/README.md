# Kelompok2 — Aulia skenario 2

Dataset khusus kelompok ini. Alur sama (lihat README utama repo).

| Item | Nilai |
|---|---|
| Skenario | Aulia skenario 2 |
| Sampel (N) | 1091 |
| Bit bersama | 227 |
| Query parity | 125 |
| ALPHA | 1.0 |
| Hash | SHA-1 |
| Kunci (SHA-1) | `6d8a6e5796d7ccebb2c45d49fbca6789d7a5d1ff` |
| Status | MATCH |

## Jalankan
1. **Bob (ESP32)**: buka `bob/bob_esp32/bob_esp32.ino`, isi WiFi, Upload, catat IP dari Serial Monitor.
2. **Alice (laptop)**: edit `alice/alice.py` -> `BOB_IP` = IP ESP32. Lalu:
   ```
   cd alice
   python alice.py
   ```
3. Output: kunci Alice = kunci Bob = `6d8a6e5796d7ccebb2c45d49fbca6789d7a5d1ff` -> **MATCH**.
