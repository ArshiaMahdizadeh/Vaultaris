"""
Vault security audit: weak/reused/old passwords, breach detection (HIBP).
"""
import hashlib
import requests
import time
from zxcvbn import zxcvbn
from src.models.item import Item, ItemType

HIBP_API = "https://api.pwnedpasswords.com/range/"
HIBP_USER_AGENT = "Vaultaris"

def analyze_vault(items: list[Item]) -> dict:
    """
    Return a dictionary with:
      - total_items
      - weak_count
      - reused_count
      - old_count
      - breach_count (set to 0 initially, filled after breach check)
      - health_score (0-100)
      - details: list of dicts with item title, issues
    """
    total = len(items)
    weak = 0
    old = 0
    now = time.time()
    details = []

    # Count password occurrences (only for password-type items with non‑empty passwords)
    password_count = {}
    for item in items:
        if item.type == ItemType.PASSWORD and item.password:
            pwd = item.password
            password_count[pwd] = password_count.get(pwd, 0) + 1

    reused_set = {pwd for pwd, count in password_count.items() if count > 1}

    for item in items:
        issues = []

        # Weak check – only for password-type items that actually have a password
        if item.type == ItemType.PASSWORD and item.password:
            try:
                strength = zxcvbn(item.password)
                if strength["score"] <= 2:
                    weak += 1
                    issues.append("Weak password")
            except Exception:
                # If zxcvbn fails for any reason, skip this item
                pass

            # Reused check
            if item.password in reused_set:
                issues.append("Reused password")

        # Old check – applied to all items
        age_days = (now - item.modified_at) / 86400
        if age_days > 90:
            old += 1
            issues.append(f"Old password ({age_days:.0f} days)")

        if issues:
            details.append({
                "title": item.title,
                "username": getattr(item, 'username', ''),
                "issues": issues
            })

    deduct = weak * 5 + len(reused_set) * 10 + old * 3
    health = max(0, 100 - deduct)

    return {
        "total_items": total,
        "weak_count": weak,
        "reused_count": len(reused_set),
        "old_count": old,
        "breach_count": 0,
        "health_score": health,
        "details": details
    }

def check_password_breach(password: str) -> int:
    """
    Check password against HIBP via k-anonymity.
    Returns the number of times the password appears in breaches (0 = safe), -1 on error.
    """
    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1_hash[:5], sha1_hash[5:]

    try:
        resp = requests.get(
            f"{HIBP_API}{prefix}",
            headers={"User-Agent": HIBP_USER_AGENT},
            timeout=5
        )
        if resp.status_code != 200:
            return -1
        for line in resp.text.splitlines():
            parts = line.split(":")
            if parts[0] == suffix:
                return int(parts[1])
        return 0
    except requests.RequestException:
        return -1