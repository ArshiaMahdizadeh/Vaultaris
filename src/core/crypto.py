"""
Crypto module: key derivation with Argon2id and AES-256-GCM encryption.
All operations use high-entropy salts/nonces from os.urandom.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type

# Argon2id parameters (tune for your target hardware)
ARGON2_TIME_COST = 3          # number of iterations
ARGON2_MEMORY_COST = 65536    # 64 MB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

AES_KEY_LEN = 32  # 256 bits
NONCE_LEN = 12    # 96 bits recommended for GCM

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit key from password and salt using Argon2id.
    Returns raw key bytes.
    """
    return hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )

def generate_salt() -> bytes:
    """Generate a cryptographically random salt."""
    return os.urandom(ARGON2_SALT_LEN)

def encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext using AES-256-GCM.
    Returns (nonce, ciphertext).
    The nonce must be stored alongside the ciphertext.
    """
    nonce = os.urandom(NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce, ciphertext

def decrypt(nonce: bytes, ciphertext: bytes, key: bytes) -> bytes:
    """Decrypt ciphertext using AES-256-GCM. Raises exception on tampering."""
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)