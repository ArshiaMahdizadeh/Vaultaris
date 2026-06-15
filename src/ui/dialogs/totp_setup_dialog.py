from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialogButtonBox, QMessageBox
)
from src.core.totp import validate_secret, generate_totp

class TotpSetupDialog(QDialog):
    def __init__(self, parent=None, current_secret: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Set up TOTP")
        self.setFixedSize(400, 200)
        self._init_ui(current_secret)

    def _init_ui(self, current_secret):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        label = QLabel("Paste the secret key or otpauth:// URI:")
        layout.addWidget(label)

        self.secret_input = QLineEdit(current_secret)
        self.secret_input.setPlaceholderText("JBSWY3DPEHPK3PXP or otpauth://...")
        layout.addWidget(self.secret_input)

        test_btn = QPushButton("Test code")
        test_btn.clicked.connect(self._test_code)
        layout.addWidget(test_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _test_code(self):
        secret = self.secret_input.text().strip()
        if not secret:
            QMessageBox.warning(self, "Error", "Enter a secret first.")
            return
        if not validate_secret(secret):
            QMessageBox.warning(self, "Error", "Invalid secret or URI.")
            return
        try:
            code = generate_totp(secret)
            QMessageBox.information(self, "Current Code", f"Current TOTP: {code}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _save(self):
        secret = self.secret_input.text().strip()
        if secret and not validate_secret(secret):
            QMessageBox.warning(self, "Error", "Invalid secret or URI. Leave blank to remove.")
            return
        if secret.startswith("otpauth://") and not secret.startswith("otpauth://totp"):
            QMessageBox.warning(self, "Error", "Only TOTP URIs are supported (otpauth://totp/...).")
            return
        self.accept()

    def get_secret(self) -> str:
        return self.secret_input.text().strip()
