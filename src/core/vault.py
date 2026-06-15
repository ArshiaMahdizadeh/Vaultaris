"""
Vault manager: handles lock/unlock, encryption/decryption of the entire item list.
Items are serialised as JSON, then encrypted with a key derived from the master password.
Now uses the unified Item model (with type field) and migrates old Credential data.
"""
import json
import os
import secrets
import tempfile
import base64
from .crypto import derive_key, generate_salt, encrypt, decrypt
from src.models.vault_meta import VaultMeta
from src.models.item import Item, ItemType


class Vault:
    def __init__(self):
        self._key: bytearray | None = None
        self._salt: bytes | None = None
        self._items: list[Item] = []
        self._file_path: str | None = None
        self.meta: VaultMeta | None = None

    @property
    def is_locked(self) -> bool:
        return self._key is None

    def _check_open(self):
        if self._key is None:
            raise RuntimeError("Vault is locked. Unlock it first.")

    def create(self, master_password: bytearray, file_path: str, progress_cb=None) -> None:
        def _report(pct, msg):
            if progress_cb:
                progress_cb(pct, msg)

        self._file_path = file_path

        _report(5, "Generating salt...")
        salt = generate_salt()

        _report(10, "Deriving encryption key (Argon2id)...")
        key = derive_key(master_password, salt)

        _report(60, "Encrypting vault data...")
        verification_plaintext = secrets.token_bytes(32)
        v_nonce, v_cipher = encrypt(verification_plaintext, bytes(key))

        _report(80, "Finalizing vault structure...")
        self.meta = VaultMeta.create(salt, (v_nonce, v_cipher))
        self._key = key
        self._salt = salt
        self._items = []

        _report(90, "Writing vault file to disk...")
        self._save()
        _report(100, "Done.")

    def open(self, master_password: bytearray, file_path: str, progress_cb=None) -> bool:
        def _report(pct, msg):
            if progress_cb:
                progress_cb(pct, msg)

        _report(5, "Reading vault metadata...")
        self._file_path = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            meta_json = f.readline().strip()
        self.meta = VaultMeta.from_json(meta_json)
        salt = self.meta.get_salt()

        _report(10, "Deriving encryption key (Argon2id)...")
        key = derive_key(master_password, salt)

        _report(60, "Verifying master password...")
        nonce, cipher = self.meta.get_verification_blob()

        verified = False
        try:
            plain = decrypt(nonce, cipher, bytes(key))
            verified = True
        except Exception:
            verified = False

        if not verified:
            _report(80, "Incorrect password — running dummy decryption...")
            dummy_key = os.urandom(32)
            dummy_nonce = os.urandom(12)
            dummy_ct = os.urandom(64)
            try:
                decrypt(dummy_nonce, dummy_ct, dummy_key)
            except Exception:
                pass
            self.meta.failure_count += 1
            self._save_meta_only()
            _report(100, "Failed.")
            return False

        _report(70, "Password verified. Decrypting items...")
        self._key = key
        self._salt = salt
        self.meta.failure_count = 0
        self._save_meta_only()
        self._load_items()
        _report(100, "Vault unlocked.")
        return True

    VALID_TYPES = {t for t in ItemType}

    def _load_items(self):
        with open(self._file_path, "r", encoding="utf-8") as f:
            f.readline()  # skip meta
            encrypted_blob = f.read()

        if not encrypted_blob.strip():
            self._items = []
            return

        nonce_b64, cipher_b64 = encrypted_blob.strip().split("\n", 1)
        nonce = base64.b64decode(nonce_b64)
        ciphertext = base64.b64decode(cipher_b64)

        aad = self.meta.to_aad_json().encode("utf-8")
        plain = decrypt(nonce, ciphertext, bytes(self._key), associated_data=aad)
        items_data = json.loads(plain)

        self._items = []
        for data in items_data:
            if "type" not in data:
                item = Item(
                    type=ItemType.PASSWORD,
                    title=data.get("title", ""),
                    url=data.get("url"),
                    username=data.get("username", ""),
                    password=data.get("password", ""),
                    notes=data.get("notes", ""),
                    totp_secret=data.get("totp_secret"),
                    tags=data.get("tags", []),
                    created_at=data.get("created_at", 0),
                    modified_at=data.get("modified_at", 0)
                )
            else:
                item = Item.model_validate(data)
            assert item.type in self.VALID_TYPES, f"Invalid item type: {item.type}"
            self._items.append(item)

    def _save_meta_only(self):
        if not self._file_path or not self.meta:
            return
        with open(self._file_path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n", 2)
        if len(lines) >= 3:
            lines[0] = self.meta.to_json()
        tmp_path = self._file_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._file_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _save(self):
        self._check_open()
        if not self._file_path:
            raise RuntimeError("No vault file path set")

        aad = self.meta.to_aad_json().encode("utf-8")
        items_json = json.dumps([item.model_dump() for item in self._items], indent=2).encode("utf-8")
        nonce, ciphertext = encrypt(items_json, bytes(self._key), associated_data=aad)

        nonce_b64 = base64.b64encode(nonce).decode()
        cipher_b64 = base64.b64encode(ciphertext).decode()

        dir_name = os.path.dirname(self._file_path) or "."
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(self.meta.to_json() + "\n")
                f.write(nonce_b64 + "\n")
                f.write(cipher_b64)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._file_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def lock(self):
        if self._key is None:
            return
        for i in range(len(self._key)):
            self._key[i] = 0
        self._key = None
        self._salt = None
        self._items = []

    def add_item(self, item: Item):
        self._check_open()
        self._items.append(item)
        self._save()

    def get_items(self) -> list[Item]:
        return self._items

    def delete_item(self, uuid: str):
        self._check_open()
        self._items = [it for it in self._items if it.uuid != uuid]
        self._save()

    def update_item(self, updated: Item):
        self._check_open()
        for idx, it in enumerate(self._items):
            if it.uuid == updated.uuid:
                self._items[idx] = updated
                self._save()
                return
        raise ValueError("Item not found")
