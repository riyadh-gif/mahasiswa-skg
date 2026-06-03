# Simplified Secret-Key-Generation (SKG) core.
# Runs identically on Alice (laptop CPython) and Bob (ESP32 MicroPython): pure Python, no numpy.
#
# Pipeline (4 langkah, mudah diajarkan):
#   1. QUANTISASI guard-band : RSSI -> bit (buang sampel ambigu di tengah)
#   2. SIFTING                : samakan posisi sampel yang dipakai kedua sisi (tukar INDEKS saja)
#   3. REKONSILIASI (Cascade) : perbaiki bit beda pakai parity + binary search -> bit jadi identik
#   4. PRIVACY AMPLIFICATION  : kunci = SHA3-256(bit) -> hapus info parity yang bocor
#
# Keamanan: yang dikirim di kanal publik hanya POSISI indeks + PARITY. Eve tak punya nilai RSSI,
# dan privacy amplification (hash) menghapus sedikit bit parity yang bocor. Beda dgn versi lama
# (seed cleartext) -> ini SKG sungguhan.

from sha3_256 import sha3_256_hex
from pcg32 import PCG32


# ---------- 1. QUANTISASI ----------
def _mean_std(v):
    n = len(v)
    m = sum(v) / n
    var = sum((x - m) * (x - m) for x in v) / n
    return m, var ** 0.5


def quantize_guardband(values, alpha=0.5):
    """RSSI -> dict{index: bit}. Sampel di pita [lo,up] dibuang (ambigu).
    alpha besar -> lebih banyak dibuang, BER lebih rendah, kunci lebih pendek."""
    m, s = _mean_std(values)
    up = m + alpha * s
    lo = m - alpha * s
    kept = {}
    for i, x in enumerate(values):
        if x >= up:
            kept[i] = 1
        elif x <= lo:
            kept[i] = 0
    return kept


# ---------- 2. SIFTING ----------
def common_positions(kept_self, kept_peer_indices):
    """Posisi yang sama-sama disimpan kedua sisi, terurut. kept_peer_indices: list indeks peer."""
    peer = set(kept_peer_indices)
    return sorted(i for i in kept_self if i in peer)


def bits_at(kept, positions):
    return [kept[i] for i in positions]


# ---------- 3. REKONSILIASI (Cascade) ----------
def _shuffle(n, seed):
    """Permutasi deterministik 0..n-1 dari seed (sama di kedua sisi)."""
    rng = PCG32(seed)
    keys = [rng.next_u32() for _ in range(n)]
    return sorted(range(n), key=lambda i: (keys[i], i))


def block_parity(bits, idxs):
    p = 0
    for i in idxs:
        p ^= bits[i]
    return p


def cascade_correct(bits_b, parity_oracle, n, passes=14, k0=4):
    """Corrector (Bob): ubah bits_b agar identik dgn referensi (Alice) via Cascade.
    parity_oracle(list_of_indices) -> parity bit Alice atas posisi tsb (lewat jaringan).
    Param fixed (k0=4, passes=14) -> konvergen ke BER=0 utk BER awal <~20% (teruji data Aulia).
    Mengembalikan (bits_b_terkoreksi, jumlah_query_parity)."""
    bits_b = list(bits_b)
    queries = 0
    k = k0
    for p in range(passes):
        perm = _shuffle(n, 1000 + p)  # permutasi pass, sama di kedua sisi (publik, aman)
        for start in range(0, n, k):
            block = perm[start:start + k]
            pa = parity_oracle(block); queries += 1
            if pa == block_parity(bits_b, block):
                continue
            # jumlah error ganjil -> binary search 1 bit salah
            lo_block = block
            while len(lo_block) > 1:
                half = len(lo_block) // 2
                left = lo_block[:half]
                pa_l = parity_oracle(left); queries += 1
                if pa_l != block_parity(bits_b, left):
                    lo_block = left
                else:
                    lo_block = lo_block[half:]
            bits_b[lo_block[0]] ^= 1  # flip bit salah
        k = min(k * 2, n)  # blok membesar tiap pass (Cascade standar)
    return bits_b, queries


# ---------- 4. KUNCI ----------
def derive_key(bits):
    """Privacy amplification: kunci akhir = SHA3-256 atas string bit."""
    return sha3_256_hex("".join(str(b) for b in bits))


def ber(a, b):
    """Bit error rate antara dua list bit (untuk laporan/uji)."""
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(1 for i in range(n) if a[i] != b[i]) / n
