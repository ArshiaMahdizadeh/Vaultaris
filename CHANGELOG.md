# Changelog

All notable changes to Vaultaris will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

---

# [2.0.0] - 2026-06-15

## Security

### Added

* Added authenticated encryption metadata binding (AAD) to vault encryption.
* Added configuration integrity protection using HMAC-SHA256.
* Added Argon2id hashing for duress passwords.
* Added startup integrity verification for bundled Material Icons font.
* Added secure memory locking using VirtualLock on Windows.
* Added per-item breach count reporting in security audits.
* Added re-authentication requirement before displaying audit results.
* Added validation for vault file structure before opening.
* Added duplicate-entry detection during imports.
* Added export password strength validation.
* Added thread-safe configuration access using locking.
* Added secure handling for clipboard restoration.
* Added automatic closure and always-on-top protection for TOTP viewer windows.

### Changed

* Replaced AES-256-GCM with XChaCha20-Poly1305 encryption.
* Increased AEAD nonce size from 12 bytes to 24 bytes.
* Bound vault metadata directly to encrypted payloads through associated authenticated data.
* Replaced predictable verification blob with cryptographically random verification data.
* Hardened unlock workflow against timing attacks.
* Hardened duress mode to avoid leaking decoy vault existence.
* Moved configuration storage to platform-appropriate user configuration directory.
* Restricted panic shortcut selection to approved secure shortcuts.
* Sanitized recent vault history to avoid storing full vault paths.
* Improved panic action to ensure cryptographic material is wiped correctly.
* Improved secure handling of master password and encryption keys in memory.
* Changed vault item validation to enforce allowed item types.
* Improved secure handling of sensitive export data.

### Removed

* Removed unsafe plain JSON export option.
* Removed duplicate core dump disabling implementation.
* Removed automatic vault save during item loading.
* Removed storage of plaintext duress passwords.

---

## Reliability

### Added

* Added atomic vault save operations using temporary files and replacement.
* Added atomic configuration write protections.
* Added explicit PDF export error handling.
* Added import file size validation for Bitwarden imports.
* Added CSV header validation before import.
* Added template and custom field count limits.

### Changed

* Replaced wall-clock timing with monotonic timing for idle detection.
* Improved TOTP refresh logic to update only when code periods change.
* Improved multi-vault recent history updates.
* Normalized vault paths before processing.
* Improved handling of sleep and resume events for auto-lock functionality.
* Improved clipboard clearing behavior across platforms.
* Improved import preview sanitization.

### Fixed

* Fixed race conditions during configuration access.
* Fixed idle timer drift caused by system clock changes.
* Fixed KeePass password field retention after import.
* Fixed incorrect handling of custom item titles.
* Fixed unlock-screen screen-capture exposure window.
* Fixed audit thread cleanup and resource leaks.
* Fixed repeated rendering of unchanged TOTP codes.
* Fixed incorrect handling of variable-length TOTP codes.
* Fixed vault locking edge cases.
* Fixed delayed startup initialization behavior.
* Fixed export preview leaking sensitive fields.

---

## Performance

### Changed

* Lazy-loaded zxcvbn dependency only when required.
* Lazy-loaded pykeepass dependency only when required.
* Reduced unnecessary TOTP widget refreshes.
* Reduced configuration write frequency during vault operations.
* Improved vault opening consistency across multiple sessions.

---

## Privacy

### Added

* Added masking of usernames in audit views.
* Added protection against accidental password disclosure in import previews.

### Changed

* Recent vault tracking now stores hashed path identifiers instead of filesystem paths.
* Sensitive fields such as seed phrases, CVVs, and private keys are excluded from exports and serialized data.

---

## Migration Notes

### Vault Format

Vault encryption has been upgraded to XChaCha20-Poly1305 and now authenticates metadata through associated authenticated data (AAD).

Existing vaults created with Vaultaris 1.x should be opened and migrated using the first Vaultaris 2.0.0 release before relying on the new format.

### Configuration

Configuration files have moved from:

`~/.vaultaris_config.json`

to:

`~/.config/vaultaris/config.json`

Users upgrading from previous releases may be prompted to migrate existing configuration data automatically.

### Exports

Plain JSON export has been removed due to security concerns.

Encrypted export formats remain supported and PDF emergency exports now use dedicated export-password-based encryption.

---

[1.0.0] - Initial Public Release
