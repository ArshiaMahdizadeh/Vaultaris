"""
Vault security audit: weak/reused/old passwords, breach detection (HIBP).
"""
import hashlib
import json
import subprocess
import sys
import time
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
      - breach_details: dict mapping item index to breach count
    """
    from zxcvbn import zxcvbn

    total = len(items)
    weak = 0
    old = 0
    now = time.time()
    details = []
    breach_details = {}

    # Count password occurrences (only for password-type items with non‑empty passwords)
    password_count = {}
    for item in items:
        if item.type == ItemType.PASSWORD and item.password:
            pwd = item.password
            password_count[pwd] = password_count.get(pwd, 0) + 1

    reused_set = {pwd for pwd, count in password_count.items() if count > 1}

    for idx, item in enumerate(items):
        issues = []

        # Weak check – only for password-type items that actually have a password
        if item.type == ItemType.PASSWORD and item.password:
            try:
                strength = zxcvbn(item.password)
                if strength["score"] <= 2:
                    weak += 1
                    issues.append("Weak password")
            except Exception:
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
                "issues": issues,
                "index": idx,
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
        "details": details,
        "breach_details": breach_details,
    }

def check_password_breach(password: str) -> int:
    """
    Check password against HIBP via k-anonymity.
    Returns the number of times the password appears in breaches (0 = safe), -1 on error.
    """
    import requests
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
    except Exception:
        return -1

def _hibp_worker():
    """Subprocess entry point: reads passwords from stdin (JSON lines), writes results to stdout."""
    import requests as _requests
    results = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            break
        password = json.loads(line)
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1_hash[:5], sha1_hash[5:]
        count = -1
        try:
            resp = _requests.get(
                f"{HIBP_API}{prefix}",
                headers={"User-Agent": HIBP_USER_AGENT},
                timeout=5
            )
            if resp.status_code == 200:
                count = 0
                for resp_line in resp.text.splitlines():
                    parts = resp_line.split(":")
                    if parts[0] == suffix:
                        count = int(parts[1])
                        break
        except Exception:
            count = -1
        results.append(count)
    json.dump(results, sys.stdout)
    sys.stdout.write("\n")
    sys.stdout.flush()

def check_passwords_breach_batch(passwords: list[str]) -> list[int]:
    """
    Check a list of passwords against HIBP by spawning a subprocess.
    Returns a list of breach counts (-1 on error for individual passwords).
    Passwords never leave the subprocess's memory in the main process.
    """
    proc = subprocess.Popen(
        [sys.executable, "-c", "from src.core.audit import _hibp_worker; _hibp_worker()"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        for pw in passwords:
            proc.stdin.write(json.dumps(pw) + "\n")
        proc.stdin.close()
        stdout, stderr = proc.communicate(timeout=120)
        if proc.returncode != 0:
            return [-1] * len(passwords)
        return json.loads(stdout.strip())
    except Exception:
        proc.kill()
        return [-1] * len(passwords)
