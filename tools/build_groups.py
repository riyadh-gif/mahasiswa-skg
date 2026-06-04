# Generate folder self-contained per kelompok (kelompok1..N).
# Tiap kelompok: kode alice+bob lengkap + dataset Alice/Bob skenario-nya sendiri.
# Pakai: python tools/build_groups.py
import os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALICE_TPL = os.path.join(ROOT, "tools", "template", "alice")   # template kode Alice
BOB_TPL = os.path.join(ROOT, "tools", "template", "bob")       # template kode Bob
sys.path.insert(0, ALICE_TPL)
import skg_common as skg

DS = r"C:\Users\riyadh\Downloads\New folder\dataset_extracted\dataset"
A = os.path.join(DS, "RSSI_ITS_AULIA")
M = os.path.join(DS, "RSSI_ITS_MITA")

# (folder, label, alice_csv, bob_csv)
GROUPS = [
    ("kelompok1", "Aulia skenario 1",
     os.path.join(A, "Alice", "skenario1_aul_its_signal_dbm.csv"),
     os.path.join(A, "Bob",   "skenario1_aul_itsjet_signal_dbm.csv")),
    ("kelompok2", "Aulia skenario 2",
     os.path.join(A, "Alice", "skenario2_aul_its_signal_dbm.csv"),
     os.path.join(A, "Bob",   "skenario2_aul_itsjet_signal_dbm.csv")),
    ("kelompok3", "Mita skenario 1",
     os.path.join(M, "Alice", "skenario1_mita_its_fix_cleaned.csv"),
     os.path.join(M, "Bob",   "skenario1_mita_itsjet_fix_cleaned.csv")),
    ("kelompok4", "Mita skenario 2",
     os.path.join(M, "Alice", "skenario2_mita_its_fix_2_cleaned.csv"),
     os.path.join(M, "Bob",   "skenario2_mita_itsjet_fix_2_cleaned.csv")),
]
ALPHA = 1.0
ALICE_CODE = ["alice.py", "skg_common.py", "pcg32.py", "net.py"]


def load_signal(path):
    """Baca kolom wlan_radio.signal_dbm (file 1 atau 2 kolom)."""
    out = []
    with open(path) as f:
        hdr = f.readline().strip().split(",")
        ci = hdr.index("wlan_radio.signal_dbm")
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(int(float(ln.split(",")[ci])))
    return out


def write_single_col(path, vals):
    with open(path, "w") as f:
        f.write("wlan_radio.signal_dbm\n")
        for v in vals:
            f.write("%d\n" % v)


def gen_header(vals, out_path):
    with open(out_path, "w") as o:
        o.write("// Dataset RSSI Bob (embedded). Auto-generate dari bob.csv.\n")
        o.write("#ifndef SYNCED_BOB_H\n#define SYNCED_BOB_H\n")
        o.write("static const int N_BOB = %d;\n" % len(vals))
        o.write("static const int RSSI_BOB[%d] = {\n" % len(vals))
        for i in range(0, len(vals), 20):
            o.write("  " + ",".join(str(x) for x in vals[i:i+20]) + ",\n")
        o.write("};\n#endif\n")


def expected_key(A_vals, B_vals):
    a = [float(x) for x in A_vals]
    b = [float(x) for x in B_vals]
    ka = skg.quantize_guardband(a, ALPHA)
    kb = skg.quantize_guardband(b, ALPHA)
    pos = skg.common_positions(ka, list(kb.keys()))
    ba = skg.bits_at(ka, pos); bb = skg.bits_at(kb, pos)
    bb2, q = skg.cascade_correct(bb, lambda idx: skg.block_parity(ba, idx), len(pos))
    return skg.derive_key(ba), len(pos), q, (skg.derive_key(ba) == skg.derive_key(bb2))


def build():
    for folder, label, ap, bp in GROUPS:
        gdir = os.path.join(ROOT, folder)
        adir = os.path.join(gdir, "alice")
        bdir = os.path.join(gdir, "bob")
        bedir = os.path.join(bdir, "bob_esp32")
        for d in (adir, bedir):
            os.makedirs(d, exist_ok=True)

        Av = load_signal(ap); Bv = load_signal(bp)
        m = min(len(Av), len(Bv)); Av = Av[:m]; Bv = Bv[:m]

        # Alice: kode + data
        for fn in ALICE_CODE:
            shutil.copy(os.path.join(ALICE_TPL, fn), os.path.join(adir, fn))
        write_single_col(os.path.join(adir, "alice.csv"), Av)

        # Bob: kode + data + header
        shutil.copy(os.path.join(BOB_TPL, "bob_esp32", "bob_esp32.ino"), os.path.join(bedir, "bob_esp32.ino"))
        shutil.copy(os.path.join(BOB_TPL, "bob_esp32", "skg.h"), os.path.join(bedir, "skg.h"))
        shutil.copy(os.path.join(BOB_TPL, "gen_header.py"), os.path.join(bdir, "gen_header.py"))
        write_single_col(os.path.join(bdir, "bob.csv"), Bv)
        gen_header(Bv, os.path.join(bedir, "synced_bob.h"))

        key, n, q, match = expected_key(Av, Bv)
        readme = os.path.join(gdir, "README.md")
        with open(readme, "w") as f:
            f.write("# %s — %s\n\n" % (folder.capitalize(), label))
            f.write("Dataset khusus kelompok ini. Alur sama (lihat README utama repo).\n\n")
            f.write("| Item | Nilai |\n|---|---|\n")
            f.write("| Skenario | %s |\n" % label)
            f.write("| Sampel (N) | %d |\n" % m)
            f.write("| Bit bersama | %d |\n" % n)
            f.write("| Query parity | %d |\n" % q)
            f.write("| ALPHA | %.1f |\n" % ALPHA)
            f.write("| Hash | SHA-1 |\n")
            f.write("| Kunci (SHA-1) | `%s` |\n" % key)
            f.write("| Status | %s |\n\n" % ("MATCH" if match else "RETRY"))
            f.write("## Jalankan\n")
            f.write("1. **Bob (ESP32)**: buka `bob/bob_esp32/bob_esp32.ino`, isi WiFi, Upload, catat IP dari Serial Monitor.\n")
            f.write("2. **Alice (laptop)**: edit `alice/alice.py` -> `BOB_IP` = IP ESP32. Lalu:\n")
            f.write("   ```\n   cd alice\n   python alice.py\n   ```\n")
            f.write("3. Output: kunci Alice = kunci Bob = `%s` -> **%s**.\n" % (key, "MATCH" if match else "RETRY"))
        print("%-10s %-18s N=%4d bit=%3d q=%3d %s key=%s" %
              (folder, label, m, n, q, "MATCH" if match else "RETRY", key))


if __name__ == "__main__":
    build()
