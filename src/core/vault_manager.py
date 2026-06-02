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

    def open_vault(self, file_path: str, password: str) -> bool:
        # If the vault is already in memory, check its state
        if file_path in self._vaults:
            vault = self._vaults[file_path]
            if not vault.is_locked:
                # Already open and unlocked – just switch to it
                self._active_path = file_path
                Config.set("active_vault", file_path)
                return True
            else:
                # Vault exists but is locked – re‑open with password
                success = vault.open(password, file_path)
                if success:
                    self._active_path = file_path
                    Config.set("active_vault", file_path)
                return success

        # Not in memory at all – create a new Vault instance and open it
        vault = Vault()
        success = vault.open(password, file_path)
        if success:
            self._vaults[file_path] = vault
            self._active_path = file_path
            self._update_recent_vaults(file_path)
            Config.set("active_vault", file_path)
        return success

    def create_vault(self, file_path: str, password: str) -> bool:
        if file_path in self._vaults:
            return False
        vault = Vault()
        vault.create(password, file_path)
        self._vaults[file_path] = vault
        self._active_path = file_path
        self._update_recent_vaults(file_path)
        Config.set("active_vault", file_path)
        return True

    def close_vault(self, file_path: str):
        if file_path in self._vaults:
            self._vaults[file_path].lock()
            del self._vaults[file_path]
        if self._active_path == file_path:
            self._active_path = None
            Config.set("active_vault", "")
        self._update_recent_vaults(remove=file_path)

    def switch_vault(self, file_path: str):
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
            recent = [p for p in recent if p != remove]
        elif file_path and file_path not in recent:
            recent.append(file_path)
        if file_path:
            # Move to end (most recent)
            recent = [p for p in recent if p != file_path] + [file_path]
        Config.set("recent_vaults", recent[-10:])