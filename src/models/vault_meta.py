from pydantic import BaseModel
import json
import base64

class VaultMeta(BaseModel):
    version: int = 1
    salt: str
    verification_nonce: str
    verification_data: str

    @classmethod
    def create(cls, salt: bytes, verification_blob: tuple[bytes, bytes]) -> "VaultMeta":
        nonce, cipher = verification_blob
        return cls(
            salt=base64.b64encode(salt).decode(),
            verification_nonce=base64.b64encode(nonce).decode(),
            verification_data=base64.b64encode(cipher).decode(),
        )

    def get_salt(self) -> bytes:
        return base64.b64decode(self.salt)

    def get_verification_blob(self) -> tuple[bytes, bytes]:
        return (
            base64.b64decode(self.verification_nonce),
            base64.b64decode(self.verification_data),
        )

    def to_json(self) -> str:
        return self.model_dump_json()  # one line

    @classmethod
    def from_json(cls, data: str) -> "VaultMeta":
        return cls.model_validate(json.loads(data))