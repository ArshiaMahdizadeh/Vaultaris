"""
Export vault credentials to various formats.
"""
import json
import base64
import io
from src.core.crypto import encrypt, derive_key, generate_salt
from src.models.vault_meta import VaultMeta
from src.models.credential import Credential
from fpdf import FPDF
import qrcode
from qrcode.image.pil import PilImage

def export_encrypted_json(items: list[Credential], master_password: str) -> str:
    """
    Export vault to an encrypted .enc file content (as string).
    This is the same format as the vault file.
    """
    # Derive key from password (new salt each time)
    salt = generate_salt()
    key = derive_key(master_password, salt)
    # Verification blob
    v_nonce, v_cipher = encrypt(b"MASTER_PASSWORD_OK", key)
    meta = VaultMeta.create(salt, (v_nonce, v_cipher))
    # Items JSON
    items_json = json.dumps([item.model_dump() for item in items], indent=2).encode('utf-8')
    nonce, ciphertext = encrypt(items_json, key)
    # Build file content
    nonce_b64 = base64.b64encode(nonce).decode()
    cipher_b64 = base64.b64encode(ciphertext).decode()
    content = meta.to_json() + "\n" + nonce_b64 + "\n" + cipher_b64
    return content

def export_plain_json(items: list[Credential]) -> str:
    """Export as plain, unencrypted JSON (dangerous)."""
    return json.dumps([item.model_dump() for item in items], indent=2)

def export_pdf_emergency_sheet(items: list[Credential], master_password: str, output_path: str) -> None:
    """
    Create a PDF containing a QR code of the encrypted vault.
    The user can print this and later scan the QR to recover the vault file.
    """
    encrypted_content = export_encrypted_json(items, master_password)
    # Generate QR code
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(encrypted_content)
    qr.make(fit=True)
    img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")
    # Save QR code to a temporary byte stream and insert into PDF
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "Emergency Recovery Sheet - Vaultaris", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 6, "Scan this QR code with the Vaultaris app to restore your vault. You will need your master password.")
    pdf.ln(5)
    # Insert QR image (centered)
    page_width = pdf.w - 2*pdf.l_margin
    qr_width = min(100, page_width)  # scale QR to fit
    x = pdf.w/2 - qr_width/2
    y = pdf.get_y()
    pdf.image(img_bytes, x=x, y=y, w=qr_width)
    pdf.output(output_path)