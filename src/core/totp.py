"""
TOTP handling: parse otpauth URIs, generate codes, validate.
"""
import pyotp

def parse_totp_uri(uri: str) -> dict:
    """
    Parse an otpauth://totp/... URI.
    Returns dict with keys: secret, issuer, name, period, digits
    """
    try:
        totp = pyotp.parse_uri(uri)
    except Exception:
        raise ValueError("Invalid otpauth URI")
    return {
        "secret": totp.secret,
        "issuer": totp.issuer,
        "name": totp.name,
        "period": totp.interval,
        "digits": totp.digits,
    }

def generate_totp(secret: str) -> str:
    """Generate the current TOTP code from a base32 secret."""
    # If it's a full URI, parse first
    if secret.startswith("otpauth://"):
        parsed = parse_totp_uri(secret)
        secret = parsed["secret"]
    totp = pyotp.TOTP(secret)
    return totp.now()

def get_totp_instance(secret: str) -> pyotp.TOTP:
    """Return a pyotp.TOTP object for the given secret/URI."""
    if secret.startswith("otpauth://"):
        return pyotp.parse_uri(secret)
    return pyotp.TOTP(secret)

def validate_secret(secret: str) -> bool:
    """Check if the secret (or URI) is valid."""
    try:
        get_totp_instance(secret)
        return True
    except Exception:
        return False