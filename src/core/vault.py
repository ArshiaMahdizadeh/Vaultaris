"""
Vault manager: handles lock/unlock, encryption/decryption of the entire item list.
Items are serialised as JSON, then encrypted with a key derived from the master password.
Now uses the unified Item model (with type field) and migrates old Credential data.
"""
import json
import os
import base64
from .crypto import derive_key, generate_salt, encrypt, decrypt
from src.models.vault_meta import VaultMeta
from src.models.item import Item, ItemType

class Vault:
    def __init__(self):
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self._items: list[Item] = []
        self._file_path: str | None = None
        self.meta: VaultMeta | None = None
        
    @property
    def is_locked(self) -> bool:
        return self._key is None

    def _check_open(self):
        """Raise an error if the vault is locked."""
        if self._key is None:
            raise RuntimeError("Vault is locked. Unlock it first.")

    def create(self, master_password: str, file_path: str) -> None:
        self._file_path = file_path
        salt = generate_salt()
        key = derive_key(master_password, salt)

        verification_plaintext = b"MASTER_PASSWORD_OK"
        v_nonce, v_cipher = encrypt(verification_plaintext, key)

        self.meta = VaultMeta.create(salt, (v_nonce, v_cipher))
        self._key = key
        self._salt = salt
        self._items = []
        self._save()

    def open(self, master_password: str, file_path: str) -> bool:
        self._file_path = file_path
        with open(file_path, "r", encoding="utf-8") as f:
            meta_json = f.readline().strip()
        self.meta = VaultMeta.from_json(meta_json)
        salt = self.meta.get_salt()
        key = derive_key(master_password, salt)

        try:
            nonce, cipher = self.meta.get_verification_blob()
            plain = decrypt(nonce, cipher, key)
            if plain != b"MASTER_PASSWORD_OK":
                return False
        except Exception:
            return False

        self._key = key
        self._salt = salt
        self._load_items()
        return True

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

        plain = decrypt(nonce, ciphertext, self._key)
        items_data = json.loads(plain)

        self._items = []
        for data in items_data:
            if "type" not in data:
                # Migration: old Credential -> Item
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
                self._items.append(item)
            else:
                self._items.append(Item.model_validate(data))

        self._save()

    def _save(self):
        self._check_open()
        if not self._file_path:
            raise RuntimeError("No vault file path set")

        items_json = json.dumps([item.model_dump() for item in self._items], indent=2).encode("utf-8")
        nonce, ciphertext = encrypt(items_json, self._key)

        nonce_b64 = base64.b64encode(nonce).decode()
        cipher_b64 = base64.b64encode(ciphertext).decode()

        with open(self._file_path, "w", encoding="utf-8") as f:
            f.write(self.meta.to_json() + "\n")
            f.write(nonce_b64 + "\n")
            f.write(cipher_b64)
            
            

    def lock(self):
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