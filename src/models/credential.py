"""
Base credential item (password entry) stored in the vault.
"""
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import time

class Credential(BaseModel):
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    url: Optional[str] = None
    username: str = ""
    password: str = ""
    notes: str = ""
    tags: list[str] = []
    totp_secret: Optional[str] = None   # TOTP secret (base32) or full otpauth URI
    created_at: float = Field(default_factory=time.time)
    modified_at: float = Field(default_factory=time.time)