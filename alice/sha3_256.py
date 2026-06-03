# SHA3-256 (Keccak) pure-Python. Output identical to CPython hashlib.sha3_256.
# Needed because MicroPython hashlib has no sha3.

_MASK = (1 << 64) - 1
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
_ROTC = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 2, 14,
         27, 41, 56, 8, 25, 43, 62, 18, 39, 61, 20, 44]
_PILN = [10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4,
         15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1]

_RATE = 136  # bytes, for SHA3-256 (1088-bit rate, 512-bit capacity)


def _rotl(x, n):
    return ((x << n) | (x >> (64 - n))) & _MASK


def _keccak_f(st):
    for rnd in range(24):
        # theta
        bc = [st[i] ^ st[i + 5] ^ st[i + 10] ^ st[i + 15] ^ st[i + 20]
              for i in range(5)]
        for i in range(5):
            t = bc[(i + 4) % 5] ^ _rotl(bc[(i + 1) % 5], 1)
            for j in range(0, 25, 5):
                st[j + i] ^= t
        # rho + pi
        t = st[1]
        for i in range(24):
            j = _PILN[i]
            prev = st[j]
            st[j] = _rotl(t, _ROTC[i])
            t = prev
        # chi
        for j in range(0, 25, 5):
            row = [st[j + i] for i in range(5)]
            for i in range(5):
                st[j + i] = row[i] ^ ((_MASK ^ row[(i + 1) % 5]) & row[(i + 2) % 5])
        # iota
        st[0] ^= _RC[rnd]


def sha3_256(data):
    if isinstance(data, str):
        data = data.encode()
    msg = bytearray(data)
    msg.append(0x06)  # SHA3 domain separation
    while len(msg) % _RATE != 0:
        msg.append(0x00)
    msg[-1] ^= 0x80  # pad10*1 final bit

    st = [0] * 25
    for off in range(0, len(msg), _RATE):
        for i in range(_RATE // 8):
            lane = int.from_bytes(msg[off + i * 8: off + i * 8 + 8], 'little')
            st[i] ^= lane
        _keccak_f(st)

    out = bytearray()
    while len(out) < 32:
        for i in range(_RATE // 8):
            out += st[i].to_bytes(8, 'little')
            if len(out) >= 32:
                break
        if len(out) < 32:
            _keccak_f(st)
    return bytes(out[:32])


def sha3_256_hex(data):
    return ''.join('%02x' % b for b in sha3_256(data))
