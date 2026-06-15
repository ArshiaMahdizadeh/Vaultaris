"""
Crypto module: key derivation with Argon2id and XChaCha20-Poly1305 encryption.
All operations use high-entropy salts/nonces from os.urandom.
"""

import hmac
import os
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from argon2.low_level import hash_secret_raw, Type

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
ARGON2_SALT_LEN = 16

KEY_LEN = 32
NONCE_LEN = 12

def derive_key(password: bytearray, salt: bytes) -> bytearray:
    """
    Derive a 256-bit key from password and salt using Argon2id.
    Accepts and returns bytearray so callers can wipe key material.
    """
    raw = hash_secret_raw(
        secret=bytes(password),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
    return bytearray(raw)

def hash_password(password: str) -> tuple[bytes, bytes]:
    """Hash a password with Argon2id. Returns (salt, hash)."""
    salt = generate_salt()
    h = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
    return salt, h

def verify_password(password: str, salt: bytes, expected_hash: bytes) -> bool:
    """Verify a password against an Argon2id hash using constant-time comparison."""
    h = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=ARGON2_HASH_LEN,
        type=Type.ID,
    )
    return hmac.compare_digest(h, expected_hash)

def generate_salt() -> bytes:
    """Generate a cryptographically random salt."""
    return os.urandom(ARGON2_SALT_LEN)

def encrypt(plaintext: bytes, key: bytes, associated_data: bytes = None) -> tuple[bytes, bytes]:
    """
    Encrypt plaintext using XChaCha20-Poly1305.
    Returns (nonce, ciphertext_with_tag).
    associated_data is authenticated but not encrypted.
    """
    nonce = os.urandom(NONCE_LEN)
    xchacha = ChaCha20Poly1305(key)
    ciphertext = xchacha.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext

def decrypt(nonce: bytes, ciphertext: bytes, key: bytes, associated_data: bytes = None) -> bytes:
    """Decrypt ciphertext using XChaCha20-Poly1305. Raises on tampering or AAD mismatch."""
    xchacha = ChaCha20Poly1305(key)
    return xchacha.decrypt(nonce, ciphertext, associated_data)