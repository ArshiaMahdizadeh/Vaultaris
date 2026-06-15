import hashlib
import os
from typing import Dict, List, Optional
from src.core.vault import Vault
from src.models.item import Item
from src.utils.config import Config

class VaultManager:
    def __init__(self):
        self._vaults: Dict[str, Vault] = {}   # file_path -> Vault
        self._active_path: Optional[str] = None

    @property
    def active_vault(self) -> Optional[Vault]:
        return self._vaults.get(self._active_path) if self._active_path else None

    @property
    def active_path(self) -> Optional[str]:
        return self._active_path

    @property
    def vault_paths(self) -> List[str]:
        return list(self._vaults.keys())

    def _ensure_active_vault(self):
        """Raise an error if no vault is currently active."""
        if self.active_vault is None:
            raise RuntimeError("No vault is active. Please open a vault first.")

    def open_vault(self, file_path: str, password: str, progress_cb=None) -> bool:
        file_path = os.path.normpath(os.path.abspath(file_path))
        pw = bytearray(password.encode("utf-8"))
        try:
            if file_path in self._vaults:
                vault = self._vaults[file_path]
                if not vault.is_locked:
                    self._active_path = file_path
                    Config.set("active_vault", file_path)
                    self._update_recent_vaults(file_path)
                    return True
                else:
                    success = vault.open(pw, file_path, progress_cb=progress_cb)
                    if success:
                        self._active_path = file_path
                        Config.set("active_vault", file_path)
                        self._update_recent_vaults(file_path)
                    return success

            vault = Vault()
            success = vault.open(pw, file_path, progress_cb=progress_cb)
            if success:
                self._vaults[file_path] = vault
                self._active_path = file_path
                self._update_recent_vaults(file_path)
                Config.set("active_vault", file_path)
            return success
        finally:
            for i in range(len(pw)):
                pw[i] = 0

    def create_vault(self, file_path: str, password: str, progress_cb=None) -> bool:
        file_path = os.path.normpath(os.path.abspath(file_path))
        if file_path in self._vaults:
            return False
        pw = bytearray(password.encode("utf-8"))
        try:
            vault = Vault()
            vault.create(pw, file_path, progress_cb=progress_cb)
            self._vaults[file_path] = vault
            self._active_path = file_path
            self._update_recent_vaults(file_path)
            Config.set("active_vault", file_path)
            return True
        finally:
            for i in range(len(pw)):
                pw[i] = 0

    def close_vault(self, file_path: str):
        file_path = os.path.normpath(os.path.abspath(file_path))
        if file_path in self._vaults:
            self._vaults[file_path].lock()
            del self._vaults[file_path]
        if self._active_path == file_path:
            self._active_path = None
            Config.set("active_vault", "")
        self._update_recent_vaults(remove=file_path)

    def switch_vault(self, file_path: str):
        file_path = os.path.normpath(os.path.abspath(file_path))
        if file_path in self._vaults:
            self._active_path = file_path
            Config.set("active_vault", file_path)

    def get_items(self) -> List[Item]:
        self._ensure_active_vault()
        return self.active_vault.get_items()

    def add_item(self, item: Item):
        self._ensure_active_vault()
        self.active_vault.add_item(item)

    def update_item(self, item: Item):
        self._ensure_active_vault()
        self.active_vault.update_item(item)

    def delete_item(self, uuid: str):
        self._ensure_active_vault()
        self.active_vault.delete_item(uuid)

    def lock_active_vault(self):
        if self.active_vault:
            self.active_vault.lock()
            self._active_path = None
            Config.set("active_vault", "")

    def _update_recent_vaults(self, file_path: str = None, remove: str = None):
        recent = Config.get("recent_vaults", [])
        if remove:
            recent = [p for p in recent
                       if not (isinstance(p, dict) and p.get("path_hash") == hashlib.sha256(remove.encode()).hexdigest()[:16])
                       and p != remove]
        elif file_path:
            entry = {
                "basename": os.path.basename(file_path),
                "path_hash": hashlib.sha256(file_path.encode()).hexdigest()[:16],
            }
            recent = [p for p in recent
                       if not (isinstance(p, dict) and p.get("path_hash") == entry["path_hash"])
                       and p != file_path]
            recent.append(entry)
        Config.set("recent_vaults", recent[-10:])
