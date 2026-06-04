# Kelompok1 — Aulia skenario 1

Dataset khusus kelompok ini. Alur sama (lihat README utama repo).

| Item | Nilai |
|---|---|
| Skenario | Aulia skenario 1 |
| Sampel (N) | 1164 |
| Bit bersama | 123 |
| Query parity | 88 |
| ALPHA | 1.0 |
| Hash | SHA-1 |
| Kunci (SHA-1) | `38ddaa94b772d15a2bbeca1075a3a41a031b23ac` |
| Status | MATCH |

## Jalankan
1. **Bob (ESP32)**: buka `bob/bob_esp32/bob_esp32.ino`, isi WiFi, Upload, catat IP dari Serial Monitor.
2. **Alice (laptop)**: edit `alice/alice.py` -> `BOB_IP` = IP ESP32. Lalu:
   ```
   cd alice
   python alice.py
   ```
3. Output: kunci Alice = kunci Bob = `38ddaa94b772d15a2bbeca1075a3a41a031b23ac` -> **MATCH**.
