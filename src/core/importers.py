"""
Import credentials from various formats.
Each function returns a list of Credential objects (unsaved).
"""
import csv
import json
import io
from src.models.credential import Credential
from pykeepass import PyKeePass

def import_csv(file_path: str, column_map: dict) -> list[Credential]:
    """
    Import from a CSV file.
    column_map: { 'title': 'TitleColName', 'url': 'UrlColName', ... }
    Returns list of Credential objects.
    """
    credentials = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cred = Credential()
            for field, col in column_map.items():
                if col and col in row:
                    setattr(cred, field, row[col].strip())
            credentials.append(cred)
    return credentials

def import_bitwarden_json(file_path: str) -> list[Credential]:
    """
    Import from Bitwarden JSON export (unencrypted).
    Expected structure: { "items": [ ... ] }
    """
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
    """
    Import from KeePass KDBX file.
    Requires the database password.
    """
    kp = PyKeePass(file_path, password=password)
    credentials = []
    for entry in kp.entries:
        cred = Credential()
        cred.title = entry.title or ''
        cred.url = entry.url or ''
        cred.username = entry.username or ''
        cred.password = entry.password or ''
        cred.notes = entry.notes or ''
        # TOTP: KeePass often stores it in custom string fields (e.g., 'TOTP Seed')
        if entry.get_custom_value('TOTP Seed'):
            cred.totp_secret = entry.get_custom_value('TOTP Seed')
        elif entry.get_custom_value('otp'):
            cred.totp_secret = entry.get_custom_value('otp')
        credentials.append(cred)
    return credentials

def import_1password_csv(file_path: str) -> list[Credential]:
    """
    Import from 1Password CSV export.
    Expected columns: Title, URL, Username, Password, Notes, OTPAuth
    """
    column_map = {
        'title': 'Title',
        'url': 'URL',
        'username': 'Username',
        'password': 'Password',
        'notes': 'Notes',
        'totp_secret': 'OTPAuth'
    }
    return import_csv(file_path, column_map)