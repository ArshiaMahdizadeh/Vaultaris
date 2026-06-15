"""
Import credentials from various formats.
Each function returns a list of Credential objects (unsaved).
"""
import csv
import json
import io
import os
from src.models.credential import Credential

def _dedup(creds: list[Credential], existing: list) -> tuple[list[Credential], int]:
    """Remove creds whose (title, username, url) already exist. Returns (filtered, skipped_count)."""
    seen = set()
    for item in existing:
        key = (item.title.lower(), getattr(item, "username", "").lower(), getattr(item, "url", "") or "")
        seen.add(key)
    filtered = []
    skipped = 0
    for c in creds:
        key = (c.title.lower(), c.username.lower(), (c.url or "").lower())
        if key in seen or key in {(x.title.lower(), x.username.lower(), (x.url or "").lower()) for x in filtered}:
            skipped += 1
            continue
        seen.add(key)
        filtered.append(c)
    return filtered, skipped

def import_csv(file_path: str, column_map: dict) -> list[Credential]:
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        sample = f.read(8192)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            if not sniffer.has_header(sample):
                raise ValueError("CSV file has no header row. Please provide a CSV with a header.")
        except csv.Error:
            pass
        reader = csv.DictReader(f)
        credentials = []
        for row in reader:
            cred = Credential()
            for field, col in column_map.items():
                if col and col in row:
                    setattr(cred, field, row[col].strip())
            credentials.append(cred)
    return credentials

def import_bitwarden_json(file_path: str) -> list[Credential]:
    max_size = 50 * 1024 * 1024  # 50 MB
    if os.path.getsize(file_path) > max_size:
        raise ValueError("File is too large (max 50 MB).")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    credentials = []
    for item in data.get('items', []):
        cred = Credential()
        cred.title = item.get('name', '')
        cred.url = item.get('login', {}).get('uris', [{}])[0].get('uri', '')
        cred.username = item.get('login', {}).get('username', '')
        cred.password = item.get('login', {}).get('password', '')
        cred.notes = item.get('notes', '')
        if item.get('login', {}).get('totp'):
            cred.totp_secret = item['login']['totp']
        credentials.append(cred)
    return credentials

def import_keepass(file_path: str, password: str) -> list[Credential]:
    from pykeepass import PyKeePass
    kp = PyKeePass(file_path, password=password)
    credentials = []
    for entry in kp.entries:
        cred = Credential()
        cred.title = entry.title or ''
        cred.url = entry.url or ''
        cred.username = entry.username or ''
        cred.password = entry.password or ''
        cred.notes = entry.notes or ''
        if entry.get_custom_value('TOTP Seed'):
            cred.totp_secret = entry.get_custom_value('TOTP Seed')
        elif entry.get_custom_value('otp'):
            cred.totp_secret = entry.get_custom_value('otp')
        credentials.append(cred)
    return credentials

def import_1password_csv(file_path: str) -> list[Credential]:
    column_map = {
        'title': 'Title',
        'url': 'URL',
        'username': 'Username',
        'password': 'Password',
        'notes': 'Notes',
        'totp_secret': 'OTPAuth'
    }
    return import_csv(file_path, column_map)
