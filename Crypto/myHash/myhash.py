import struct
from typing import Iterable

MASK32 = 0xFFFFFFFF
MASK64 = 0xFFFFFFFFFFFFFFFF

INIT_STATE = (
    0x31415926,
    0x27182818,
    0x16180339,
    0x57721566,
)

S = (
    [3, 7, 11, 19] * 4
    + [5, 9, 13, 21] * 4
    + [4, 10, 14, 23] * 4
    + [6, 12, 18, 22] * 4
)

K = [((0x9E3779B9 * (i + 1)) ^ 0xA5A5A5A5) & MASK32 for i in range(64)]


def _rol32(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & MASK32


def md_style_padding(message_len: int, pad_lead: int = 0x80) -> bytes:
    bit_len = (message_len * 8) & MASK64
    pad_zero_len = (56 - ((message_len + 1) % 64)) % 64
    return bytes([pad_lead]) + (b"\x00" * pad_zero_len) + struct.pack("<Q", bit_len)


class WHUHash128:
    digest_size = 16
    block_size = 64

    def __init__(
        self,
        state: Iterable[int] | bytes | None = None,
        count: int = 0,
        pad_lead: int = 0x80,
    ):
        if state is None:
            self._a, self._b, self._c, self._d = INIT_STATE
        elif isinstance(state, (bytes, bytearray)):
            if len(state) != 16:
                raise ValueError("state bytes must be exactly 16 bytes")
            self._a, self._b, self._c, self._d = struct.unpack("<4I", state)
        else:
            t = tuple(state)
            if len(t) != 4:
                raise ValueError("state tuple must contain 4 words")
            self._a, self._b, self._c, self._d = [x & MASK32 for x in t]

        if count < 0:
            raise ValueError("count must be non-negative")
        if not (0 <= pad_lead <= 0xFF):
            raise ValueError("pad_lead must be in [0, 255]")
        self._count = count
        self._buffer = b""
        self._pad_lead = pad_lead

    def copy(self) -> "WHUHash128":
        h = WHUHash128((self._a, self._b, self._c, self._d), self._count, self._pad_lead)
        h._buffer = self._buffer
        return h

    def _compress(self, block: bytes) -> None:
        if len(block) != 64:
            raise ValueError("block size must be 64 bytes")

        x = struct.unpack("<16I", block)
        a, b, c, d = self._a, self._b, self._c, self._d

        for i in range(64):
            if i < 16:
                f = (b ^ (c | (~d & MASK32))) & MASK32
                g = (5 * i + 1) & 15
            elif i < 32:
                f = ((d & b) | ((~d & MASK32) & c)) & MASK32
                g = (3 * i + 5) & 15
            elif i < 48:
                f = (b ^ c ^ d) & MASK32
                g = (7 * i) & 15
            else:
                f = (c ^ (b | (~d & MASK32))) & MASK32
                g = (11 * i + 9) & 15

            t = (a + f + x[g] + K[i]) & MASK32
            t = _rol32(t, S[i])
            t = (t + b) & MASK32
            a, b, c, d = d, t, b, c

        self._a = (self._a + a) & MASK32
        self._b = (self._b + b) & MASK32
        self._c = (self._c + c) & MASK32
        self._d = (self._d + d) & MASK32

        # Extra cross-mixing so this is visibly different from MD5 internals.
        na = (self._a ^ _rol32(self._c, 3)) & MASK32
        nb = (self._b + _rol32(self._d, 7)) & MASK32
        nc = (self._c ^ _rol32(self._a, 13)) & MASK32
        nd = (self._d + _rol32(self._b, 17)) & MASK32
        self._a, self._b, self._c, self._d = na, nb, nc, nd

    def update(self, data: bytes) -> "WHUHash128":
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if not data:
            return self

        self._count += len(data)
        self._buffer += bytes(data)

        while len(self._buffer) >= 64:
            self._compress(self._buffer[:64])
            self._buffer = self._buffer[64:]
        return self
    
    def _finalize(self) -> bytes:
        self.update(md_style_padding(self._count, self._pad_lead))
        if self._buffer:
            raise RuntimeError("buffer must be empty after finalization")
        return struct.pack("<4I", self._a, self._b, self._c, self._d)

    def digest(self) -> bytes:
        return self.copy()._finalize()

    def hexdigest(self) -> str:
        return self.digest().hex()


def whu_md5(data: bytes, pad_lead: int = 0x80) -> bytes:
    return WHUHash128(pad_lead=pad_lead).update(data).digest()


def whu_md5_hex(data: bytes, pad_lead: int = 0x80) -> str:
    return whu_md5(data, pad_lead=pad_lead).hex()
