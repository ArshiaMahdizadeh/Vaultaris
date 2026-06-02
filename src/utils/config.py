import json
import os

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".vaultaris_config.json")

DEFAULT_CONFIG = {
    "idle_timeout_minutes": 5,
    "lock_on_idle": True,
    "lock_on_sleep": True,
    "recent_vaults": [],
    "active_vault": "",
    # Advanced security
    "duress_enabled": False,
    "duress_password": "",
    "decoy_vault_path": "",
    "block_screen_capture": True,
    "lock_memory": True,
    "panic_shortcut": "Ctrl+Shift+L",
    # Theme
    "theme": "dark",
    # Custom templates
    "custom_templates": []
}


class Config:
    _data = None

    @classmethod
    def load(cls):
        if cls._data is not None:
            return cls._data
        try:
            with open(CONFIG_PATH, "r") as f:
                cls._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cls._data = DEFAULT_CONFIG.copy()

        # Migration: ensure idle timeout is at least 2 minutes
        if cls._data.get("idle_timeout_minutes", 5) < 2:
            cls._data["idle_timeout_minutes"] = 5
            cls.save()

        # Migration: ensure theme field exists (for older configs)
        if "theme" not in cls._data:
            cls._data["theme"] = "dark"
            cls.save()

        if "custom_templates" not in cls._data:
            cls._data["custom_templates"] = []
            cls.save()

        return cls._data

    @classmethod
    def save(cls):
        with open(CONFIG_PATH, "w") as f:
            json.dump(cls._data or DEFAULT_CONFIG, f, indent=2)

    @classmethod
    def get(cls, key, default=None):
        return cls.load().get(key, default)

    @classmethod
    def set(cls, key, value):
        cls.load()[key] = value
        cls.save()

    @classmethod
    def reset(cls):
        cls._data = DEFAULT_CONFIG.copy()
        cls.save()