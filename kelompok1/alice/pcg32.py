# PCG32 — deterministic PRNG, identical output on ESP32 (MicroPython) and PC (CPython).
# Pure integer math only -> no float divergence between single/double precision.
# Used to derive the shared random permutation from the shared seed.

_MASK64 = (1 << 64) - 1
_MASK32 = (1 << 32) - 1
_MULT = 6364136223846793005


class PCG32:
    def __init__(self, seed, seq=54):
        # Matches the reference pcg32_srandom_r initialization.
        self.state = 0
        self.inc = ((seq << 1) | 1) & _MASK64
        self._step()
        self.state = (self.state + (seed & _MASK64)) & _MASK64
        self._step()

    def _step(self):
        self.state = (self.state * _MULT + self.inc) & _MASK64

    def next_u32(self):
        old = self.state
        self._step()
        xorshifted = (((old >> 18) ^ old) >> 27) & _MASK32
        rot = old >> 59
        return ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & _MASK32


def permutation_keys(seed, n):
    """Return list of n 32-bit integer keys. argsort on these == shared permutation.

    Identical on every platform because only integer ops are used.
    """
    rng = PCG32(seed)
    return [rng.next_u32() for _ in range(n)]


def argsort_keys(keys):
    """Stable argsort by (key, index). Deterministic tie-break -> cross-platform safe."""
    return sorted(range(len(keys)), key=lambda i: (keys[i], i))
