"""
Export vault credentials to various formats.
"""
import json
import secrets
import base64
import io
from src.core.crypto import encrypt, derive_key, generate_salt
from src.models.vault_meta import VaultMeta
from src.models.credential import Credential
from fpdf import FPDF
import qrcode
from qrcode.image.pil import PilImage


def export_encrypted_json(items: list[Credential], master_password: str) -> str:
    salt = generate_salt()
    key = derive_key(bytearray(master_password.encode("utf-8")), salt)

    verification_plaintext = secrets.token_bytes(32)
    v_nonce, v_cipher = encrypt(verification_plaintext, bytes(key))
    meta = VaultMeta.create(salt, (v_nonce, v_cipher))

    aad = meta.to_aad_json().encode("utf-8")
    items_json = json.dumps([item.model_dump() for item in items], indent=2).encode('utf-8')
    nonce, ciphertext = encrypt(items_json, bytes(key), associated_data=aad)

    nonce_b64 = base64.b64encode(nonce).decode()
    cipher_b64 = base64.b64encode(ciphertext).decode()
    content = meta.to_json() + "\n" + nonce_b64 + "\n" + cipher_b64
    return content

def export_pdf_emergency_sheet(items: list[Credential], export_password: str, output_path: str) -> None:
    salt = generate_salt()
    key = derive_key(bytearray(export_password.encode("utf-8")), salt)

    encrypted_items = []
    for item in items:
        item_json = json.dumps(item.model_dump(), indent=2).encode("utf-8")
        nonce, ciphertext = encrypt(item_json, bytes(key))
        encrypted_items.append({
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        })

    export_data = {
        "salt": base64.b64encode(salt).decode(),
        "items": encrypted_items,
    }
    encrypted_content = json.dumps(export_data)

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(encrypted_content)
    qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    try:
        pdf.cell(0, 10, "Emergency Recovery Sheet - Vaultaris", ln=True, align='C')
    except Exception as e:
        raise RuntimeError(f"Failed to write PDF header: {e}")
    pdf.ln(10)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, "Scan this QR code with the Vaultaris app to restore your vault. You will need your export password.")
    pdf.ln(5)
    page_width = pdf.w - 2*pdf.l_margin
    qr_width = min(100, page_width)
    x = pdf.w/2 - qr_width/2
    y = pdf.get_y()
    try:
        pdf.image(img_bytes, x=x, y=y, w=qr_width)
    except Exception as e:
        raise RuntimeError(f"Failed to embed QR code image in PDF: {e}")
    pdf.output(output_path)
