# Praktikum SKG — Secret-Key-Generation Sederhana (Alice ↔ Bob)

![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/perangkat-ESP32-blue)
![Lang](https://img.shields.io/badge/bahasa-Python%20%7C%20C%2B%2B-orange)
![Hash](https://img.shields.io/badge/hash-SHA--1-yellow)
![Status](https://img.shields.io/badge/status-teruji%20MATCH-brightgreen)

Dua perangkat mengukur sinyal WiFi (RSSI) kanal yang sama, lalu **menghasilkan kunci rahasia
yang identik tanpa pernah mengirim kunci itu**. Eve (penyadap) tidak bisa menurunkan kunci
karena yang lewat kanal publik hanya posisi indeks + parity, bukan nilai RSSI.

- **Alice** = laptop (Python)
- **Bob** = ESP32 (Arduino C++)

![Alur protokol SKG](docs/diagram.png)

---

## Pembagian kelompok (dataset berbeda tiap kelompok)

Tiap kelompok memakai **pasangan RSSI Alice+Bob berbeda** dan menghasilkan **kunci berbeda**.

| Kelompok | Dataset | Sampel | Bit bersama | Kunci (SHA-1) |
|---|---|---|---|---|
| **1** | Aulia skenario 1 | 1164 | 123 | `38ddaa94b772d15a2bbeca1075a3a41a031b23ac` |
| **2** | Aulia skenario 2 | 1091 | 227 | `6d8a6e5796d7ccebb2c45d49fbca6789d7a5d1ff` |
| **3** | Mita skenario 1  | 1177 | 185 | `55926ef8eb8588dbd5fa32c158198fb3029d1525` |
| **4** | Mita skenario 2  | 1180 | 243 | `a5e339f71c616fa16b7d48d2db3a035eee43fc2d` |

Tiap kelompok cukup buka folder `kelompokN/` masing-masing — sudah lengkap (kode + dataset).

---

## 1. Konsep (4 langkah)

| Langkah | Apa yang terjadi |
|---|---|
| 1. **Quantisasi guard-band** | RSSI → bit (0/1). Sampel ambigu di tengah (mean ± α·std) dibuang. |
| 2. **Sifting** | Tukar **posisi** sampel yang dipakai; ambil irisan. (posisi = aman dibagi) |
| 3. **Rekonsiliasi (Cascade)** | Perbaiki bit yang beda pakai parity + binary search → bit jadi identik. |
| 4. **Privacy amplification** | Kunci = **SHA-1**(bit). Menghapus info parity yang sempat bocor. |

Verifikasi akhir: tukar `H(H(kunci))` → **MATCH** / **RETRY**.

> Catatan: SHA-1 dipakai untuk tujuan ajar/perbandingan. SHA-1 sudah deprecated (rawan kolusi);
> untuk keamanan nyata gunakan SHA-2/SHA-3.

---

## 2. Alat yang dibutuhkan

**Laptop (Alice):** Python 3.8+ (tanpa library tambahan).
**ESP32 (Bob):** Arduino IDE / `arduino-cli`, board package **esp32**, kabel USB.
**Jaringan:** satu WiFi/hotspot **2.4 GHz** untuk laptop + ESP32 (hindari WiFi kampus / 5 GHz).

---

## 3. Struktur repo

```
mahasiswa-skg/
├── kelompok1/  (Aulia skenario 1)
│   ├── alice/  alice.py, skg_common.py, pcg32.py, net.py, alice.csv
│   ├── bob/    bob_esp32/{bob_esp32.ino, skg.h, synced_bob.h}, bob.csv, gen_header.py
│   └── README.md
├── kelompok2/ ...  kelompok3/ ...  kelompok4/ ...
├── docs/       praktikum.tex/pdf, diagram.png
├── tools/      template/ (kode sumber), build_groups.py (regen folder kelompok)
├── LICENSE
└── README.md
```

---

## 4. Langkah praktikum (per kelompok)

### A. Jaringan
Nyalakan hotspot HP (2.4 GHz). Sambungkan laptop ke hotspot itu.

### B. Bob (ESP32) — Arduino IDE
1. Tambah board URL (Preferences): `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
   lalu Boards Manager → install **esp32**.
2. Buka `kelompokN/bob/bob_esp32/bob_esp32.ino`, isi WiFi:
   ```cpp
   const char* WIFI_SSID = "NAMA_HOTSPOT";
   const char* WIFI_PASS = "PASSWORD_HOTSPOT";
   ```
3. Board = **ESP32 Dev Module**, pilih Port, **Upload**.
4. Buka **Serial Monitor** (115200), catat `IP ESP32`.

### C. Alice (laptop)
Edit `kelompokN/alice/alice.py` → `BOB_IP` = IP ESP32. Pastikan `ALPHA` sama (default 1.0).

### D. Jalankan
```
cd kelompokN/alice
python alice.py
```

### E. Hasil benar (contoh kelompok 1)
```
Kunci Alice : 38ddaa94b772d15a2bbeca1075a3a41a031b23ac
Kunci Bob   : 38ddaa94b772d15a2bbeca1075a3a41a031b23ac
Sama?       : YA
Status      : MATCH
```
Kunci tiap kelompok beda (lihat tabel di atas / `kelompokN/README.md`).

---

## 5. Troubleshooting

| Gejala | Solusi |
|---|---|
| ESP32 cetak titik terus | WiFi salah / 5 GHz → cek SSID/pass, pakai 2.4 GHz |
| Alice `Gagal connect` | IP ESP32 salah / beda WiFi → samakan WiFi, perbarui `BOB_IP` |
| Alice menggantung lalu gagal | client isolation → pakai hotspot HP |
| `STATUS: RETRY` | kanal bising → naikkan `ALPHA` di kedua sisi |
| Port COM tak terbuka | tutup Serial Monitor sebelum upload |

---

## 6. Untuk instruktur

Regenerasi folder kelompok dari dataset mentah:
```
python tools/build_groups.py
```
Ubah daftar `GROUPS` di skrip untuk ganti skenario/kelompok. Template kode ada di
`tools/template/`. Catatan ilmiah (keamanan, entropi, ALPHA) ada di `docs/praktikum.pdf`.
