import hashlib
import hmac
import json
import os
import platform
import threading

_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "vaultaris")
CONFIG_PATH = os.path.join(_CONFIG_DIR, "config.json")

ALLOWED_PANIC_SHORTCUTS = [
    "Ctrl+Shift+P",
    "Ctrl+Shift+Escape",
    "Ctrl+Shift+L",
]

DEFAULT_CONFIG = {
    "idle_timeout_minutes": 5,
    "lock_on_idle": True,
    "lock_on_sleep": True,
    "recent_vaults": [],
    "active_vault": "",
    # Advanced security
    "duress_enabled": False,
    "duress_password_hash": "",
    "duress_password_salt": "",
    "decoy_vault_path": "",
    "block_screen_capture": True,
    "lock_memory": True,
    "panic_shortcut": "Ctrl+Shift+L",
    # Theme
    "theme": "dark",
    # Custom templates
    "custom_templates": []
}


def _machine_key() -> bytes:
    """Derive a machine-specific key for config HMAC."""
    raw = (platform.node() + platform.machine() + os.path.expanduser("~")).encode("utf-8")
    return hashlib.sha256(raw).digest()


def _compute_hmac(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, indent=2).encode("utf-8")
    return hmac.new(_machine_key(), payload, hashlib.sha256).hexdigest()


class Config:
    _data = None
    _lock = threading.RLock()
    _hmac: str | None = None

    @classmethod
    def load(cls):
        with cls._lock:
            if cls._data is not None:
                return cls._data
            try:
                with open(CONFIG_PATH, "r") as f:
                    cls._data = json.load(f)
                stored_hmac = cls._data.pop("_hmac", None)
                if stored_hmac:
                    computed = _compute_hmac(cls._data)
                    if not hmac.compare_digest(stored_hmac, computed):
                        cls._data = DEFAULT_CONFIG.copy()
                cls._hmac = stored_hmac
            except (FileNotFoundError, json.JSONDecodeError):
                cls._data = DEFAULT_CONFIG.copy()

            # Migration: ensure idle timeout is at least 2 minutes
            if cls._data.get("idle_timeout_minutes", 5) < 2:
                cls._data["idle_timeout_minutes"] = 5
                cls._save_unlocked()

            # Migration: ensure theme field exists (for older configs)
            if "theme" not in cls._data:
                cls._data["theme"] = "dark"
                cls._save_unlocked()

            if "custom_templates" not in cls._data:
                cls._data["custom_templates"] = []
                cls._save_unlocked()

            return cls._data

    @classmethod
    def _save_unlocked(cls):
        os.makedirs(_CONFIG_DIR, mode=0o700, exist_ok=True)
        data_to_save = dict(cls._data or DEFAULT_CONFIG)
        data_to_save["_hmac"] = _compute_hmac(data_to_save)
        content = json.dumps(data_to_save, indent=2)
        fd = os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(content)
        except Exception:
            os.close(fd)
            raise

    @classmethod
    def save(cls):
        with cls._lock:
            cls._save_unlocked()

    @classmethod
    def get(cls, key, default=None):
        return cls.load().get(key, default)

    @classmethod
    def set(cls, key, value):
        with cls._lock:
            cls.load()
            cls._data[key] = value
            cls._save_unlocked()

    @classmethod
    def reset(cls):
        with cls._lock:
            cls._data = DEFAULT_CONFIG.copy()
            cls._save_unlocked()
