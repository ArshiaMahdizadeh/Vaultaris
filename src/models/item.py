from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
import uuid
import time

class ItemType(str, Enum):
    PASSWORD = "password"
    NOTE = "note"
    CREDIT_CARD = "credit_card"
    IDENTITY = "identity"
    WIFI = "wifi"
    LICENSE = "license"
    CRYPTO_SEED = "crypto_seed"
    CUSTOM = "custom"

class Item(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ItemType = ItemType.PASSWORD
    title: str = ""
    url: Optional[str] = None
    username: str = ""
    password: str = ""
    notes: str = ""                     # plain text or markdown for notes
    totp_secret: Optional[str] = None
    # Type‑specific fields
    card_number: Optional[str] = None
    card_holder: Optional[str] = None
    card_expiry: Optional[str] = None
    card_cvv: Optional[str] = None
    id_firstname: Optional[str] = None
    id_lastname: Optional[str] = None
    id_email: Optional[str] = None
    id_phone: Optional[str] = None
    id_address: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    wifi_security: Optional[str] = None
    license_key: Optional[str] = None
    license_vendor: Optional[str] = None
    crypto_seed_phrase: Optional[str] = None
    crypto_wallet_type: Optional[str] = None
    # Custom template fields
    custom_template_id: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    modified_at: float = Field(default_factory=time.time)