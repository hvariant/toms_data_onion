# lifted from https://cryptography.io/en/latest/_modules/cryptography/hazmat/primitives/keywrap/#aes_key_unwrap

import struct

from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import ECB, CBC
from cryptography.hazmat.primitives.constant_time import bytes_eq
from cryptography.hazmat.backends import default_backend


backend = default_backend()

def unwrap_core(wrapping_key, a, r):
    # Implement RFC 3394 Key Unwrap - 2.2.2 (index method)
    decryptor = Cipher(AES(wrapping_key), ECB(), backend).decryptor()
    n = len(r)
    for j in reversed(range(6)):
        for i in reversed(range(n)):
            # pack/unpack are safe as these are always 64-bit chunks
            atr = struct.pack(
                ">Q", struct.unpack(">Q", a)[0] ^ ((n * j) + i + 1)
            ) + r[i]
            # every decryption operation is a discrete 16 byte chunk so
            # it is safe to reuse the decryptor for the entire operation
            b = decryptor.update(atr)
            a = b[:8]
            r[i] = b[-8:]

    assert decryptor.finalize() == b""
    return a, r

def aes_key_unwrap(wrapping_key, wrapped_key, aiv):
    if len(wrapped_key) < 24:
        raise InvalidUnwrap("Must be at least 24 bytes")

    if len(wrapped_key) % 8 != 0:
        raise InvalidUnwrap("The wrapped key must be a multiple of 8 bytes")

    if len(wrapping_key) not in [16, 24, 32]:
        raise ValueError("The wrapping key must be a valid AES key length")

    r = [wrapped_key[i:i + 8] for i in range(0, len(wrapped_key), 8)]
    a = r.pop(0)
    a, r = unwrap_core(wrapping_key, a, r)
    if not bytes_eq(a, aiv):
        raise InvalidUnwrap()

    return b"".join(r)

def aes_decrypt(key, iv, ct):
    cipher = Cipher(AES(key), CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    return decryptor.update(ct) + decryptor.finalize()


class InvalidUnwrap(Exception):
    pass
