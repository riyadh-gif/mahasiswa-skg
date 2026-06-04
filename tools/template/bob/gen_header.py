# Regenerasi synced_bob.h dari bob.csv.
# Pakai: python gen_header.py
# Dataset RSSI di-embed jadi C array supaya ESP32 (Arduino) tak perlu filesystem.

SRC = "bob.csv"
OUT = "bob_esp32/synced_bob.h"

vals = []
with open(SRC) as f:
    next(f)  # header
    for ln in f:
        ln = ln.strip()
        if ln:
            vals.append(int(float(ln)))

with open(OUT, "w") as o:
    o.write("// Dataset RSSI Bob (Aulia synced) di-embed. Auto-generate dari synced_bob.csv.\n")
    o.write("#ifndef SYNCED_BOB_H\n#define SYNCED_BOB_H\n")
    o.write("static const int N_BOB = %d;\n" % len(vals))
    o.write("static const int RSSI_BOB[%d] = {\n" % len(vals))
    for i in range(0, len(vals), 20):
        o.write("  " + ",".join(str(x) for x in vals[i:i+20]) + ",\n")
    o.write("};\n#endif\n")

print("written", len(vals), "samples ->", OUT)
