# ALICE (laptop, CPython). Client + reference side of simplified SKG.
# Run: python alice.py   (jalankan SETELAH ESP32 Bob menyala & cetak IP-nya)
import skg_common as skg
import net

# --- config (HARUS sama dgn bob_esp32.ino) ---
PORT = 6000
BOB_IP = "GANTI_IP_ESP32"   # IP ESP32 (lihat Serial Monitor Arduino), mis. 192.168.100.124
ALPHA = 1.0                  # guard band; HARUS sama dgn ALPHA di bob_esp32.ino
CSV = "synced_alice.csv"     # dataset Alice (di folder ini)


def load_rssi(path):
    vals = []
    with open(path) as f:
        next(f)  # header
        for ln in f:
            ln = ln.strip()
            if ln:
                vals.append(float(ln))
    return vals


def main():
    rssi = load_rssi(CSV)
    kept = skg.quantize_guardband(rssi, ALPHA)   # {index: bit}
    print("Alice: N=%d, kept(quantisasi)=%d" % (len(rssi), len(kept)))

    # Alice = TCP client, connect ke ESP32 (Bob = server)
    link = net.connect(BOB_IP, PORT)

    # 1. SIFTING: terima indeks Bob, hitung posisi bersama, kirim balik
    bob_idx = [int(x) for x in link.recvline().split(",") if x != ""]
    pos = skg.common_positions(kept, bob_idx)
    link.sendline(",".join(str(i) for i in pos))
    bits_a = skg.bits_at(kept, pos)
    n = len(pos)
    print("Sifting: posisi bersama =", n)

    # 2. REKONSILIASI: jawab query parity dari Bob sampai Bob kirim "DONE"
    while True:
        msg = link.recvline()
        if msg is None or msg == "DONE":
            break
        idxs = [int(x) for x in msg.split(",") if x != ""]
        link.sendline(str(skg.block_parity(bits_a, idxs)))

    # 3. KUNCI + verifikasi
    key = skg.derive_key(bits_a)
    hh = skg.sha3_256_hex(key)              # H(H(bits)) untuk verifikasi
    link.sendline(hh)
    status = link.recvline()
    print("Kunci Alice :", key)
    print("Status      :", status)
    link.close()


if __name__ == "__main__":
    main()
