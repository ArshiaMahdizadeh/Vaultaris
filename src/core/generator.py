"""
Password generator: random characters, passphrases, strength estimation.
Uses secrets module for cryptographically strong randomness.
"""
import secrets
import string
import math
from zxcvbn import zxcvbn

# Default wordlist (EFF large list – first 50 words; replace with full list later)
DEFAULT_WORDLIST = [
    "abacus", "abdomen", "abdominal", "abide", "abiding", "ability", "ablaze",
    "able", "abnormal", "abrasion", "abrasive", "abreast", "abridge", "abroad",
    "abruptly", "absence", "absentee", "absently", "absinthe", "absolute",
    "absolve", "abstain", "abstract", "absurd", "accent", "acclaim", "acclimate",
    "accompany", "account", "accuracy", "accurate", "accustom", "acetone",
    "achiness", "aching", "acid", "acorn", "acquaint", "acquire", "acre",
    "acrobat", "acronym", "acting", "action", "activate", "activator", "active",
    "activism", "activist", "activity", "actress", "acts", "actually", "acute"
]

def generate_password(
    length: int = 20,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = True,
    custom_charset: str = ""
) -> str:
    """Generate a random character password."""
    charset = ""
    if use_lower:
        charset += string.ascii_lowercase
    if use_upper:
        charset += string.ascii_uppercase
    if use_digits:
        charset += string.digits
    if use_symbols:
        charset += "!@#$%^&*"
    if custom_charset:
        charset += custom_charset

    if exclude_ambiguous:
        ambiguous = "O0Il1|`"
        charset = "".join(c for c in charset if c not in ambiguous)

    if not charset:
        raise ValueError("No character set selected")

    return "".join(secrets.choice(charset) for _ in range(length))

def generate_passphrase(
    word_count: int = 4,
    separator: str = "-",
    capitalize: bool = False,
    append_number: bool = False,
    wordlist: list[str] = None
) -> str:
    """Generate a passphrase from a wordlist."""
    if wordlist is None:
        wordlist = DEFAULT_WORDLIST
    words = [secrets.choice(wordlist) for _ in range(word_count)]
    if capitalize:
        words = [w.capitalize() for w in words]
    phrase = separator.join(words)
    if append_number:
        phrase += str(secrets.randbelow(10))
    return phrase

def calculate_entropy(password: str) -> float:
    """Estimate entropy based on character pool size and length (not perfect, but indicative)."""
    pools = 0
    if any(c.islower() for c in password):
        pools += 26
    if any(c.isupper() for c in password):
        pools += 26
    if any(c.isdigit() for c in password):
        pools += 10
    if any(c in "!@#$%^&*" for c in password):
        pools += 8
    if pools == 0:
        pools = 26
    return len(password) * math.log2(pools)

def estimate_strength(password: str) -> dict:
    """Return zxcvbn score (0-4) and crack time."""
    result = zxcvbn(password)
    crack_time = result["crack_times_display"]["offline_fast_hashing_1e10_per_second"]
    return {
        "score": result["score"],
        "crack_time": crack_time,
        "feedback": result["feedback"]["suggestions"]
    }