# Kelompok4 — Mita skenario 2

Dataset khusus kelompok ini. Alur sama (lihat README utama repo).

| Item | Nilai |
|---|---|
| Skenario | Mita skenario 2 |
| Sampel (N) | 1180 |
| Bit bersama | 243 |
| Query parity | 132 |
| ALPHA | 1.0 |
| Hash | SHA-1 |
| Kunci (SHA-1) | `a5e339f71c616fa16b7d48d2db3a035eee43fc2d` |
| Status | MATCH |

## Jalankan
1. **Bob (ESP32)**: buka `bob/bob_esp32/bob_esp32.ino`, isi WiFi, Upload, catat IP dari Serial Monitor.
2. **Alice (laptop)**: edit `alice/alice.py` -> `BOB_IP` = IP ESP32. Lalu:
   ```
   cd alice
   python alice.py
   ```
3. Output: kunci Alice = kunci Bob = `a5e339f71c616fa16b7d48d2db3a035eee43fc2d` -> **MATCH**.
