# Kelompok3 — Mita skenario 1

Dataset khusus kelompok ini. Alur sama (lihat README utama repo).

| Item | Nilai |
|---|---|
| Skenario | Mita skenario 1 |
| Sampel (N) | 1177 |
| Bit bersama | 185 |
| Query parity | 112 |
| ALPHA | 1.0 |
| Hash | SHA-1 |
| Kunci (SHA-1) | `55926ef8eb8588dbd5fa32c158198fb3029d1525` |
| Status | MATCH |

## Jalankan
1. **Bob (ESP32)**: buka `bob/bob_esp32/bob_esp32.ino`, isi WiFi, Upload, catat IP dari Serial Monitor.
2. **Alice (laptop)**: edit `alice/alice.py` -> `BOB_IP` = IP ESP32. Lalu:
   ```
   cd alice
   python alice.py
   ```
3. Output: kunci Alice = kunci Bob = `55926ef8eb8588dbd5fa32c158198fb3029d1525` -> **MATCH**.
