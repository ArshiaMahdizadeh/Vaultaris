import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QGroupBox, QGridLayout, QApplication,
)
from PyQt6.QtCore import QTimer      
from PyQt6.QtCore import Qt
from src.core.generator import generate_password, generate_passphrase, estimate_strength

class GeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password Generator")
        self.setMinimumWidth(400)
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self._clear_clipboard)
        self._init_ui()
        self._generate()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        self.preview_edit = QLineEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_edit.setMinimumHeight(50)
        layout.addWidget(self.preview_edit)

        self.strength_label = QLabel("Strength: --")
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.strength_label)

        group = QGroupBox("Settings")
        grid = QGridLayout()
        grid.addWidget(QLabel("Length:"), 0, 0)
        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 128)
        self.length_spin.setValue(20)
        self.length_spin.valueChanged.connect(self._generate)
        grid.addWidget(self.length_spin, 0, 1)

        self.upper_check = QCheckBox("A-Z")
        self.upper_check.setChecked(True)
        self.upper_check.stateChanged.connect(self._generate)
        grid.addWidget(self.upper_check, 1, 0)
        self.lower_check = QCheckBox("a-z")
        self.lower_check.setChecked(True)
        self.lower_check.stateChanged.connect(self._generate)
        grid.addWidget(self.lower_check, 1, 1)
        self.digits_check = QCheckBox("0-9")
        self.digits_check.setChecked(True)
        self.digits_check.stateChanged.connect(self._generate)
        grid.addWidget(self.digits_check, 2, 0)
        self.symbols_check = QCheckBox("!@#$%^&*")
        self.symbols_check.setChecked(True)
        self.symbols_check.stateChanged.connect(self._generate)
        grid.addWidget(self.symbols_check, 2, 1)
        self.ambiguous_check = QCheckBox("Exclude ambiguous (O0Il1)")
        self.ambiguous_check.setChecked(True)
        self.ambiguous_check.stateChanged.connect(self._generate)
        grid.addWidget(self.ambiguous_check, 3, 0, 1, 2)
        self.passphrase_mode = QCheckBox("Passphrase mode")
        self.passphrase_mode.stateChanged.connect(self._generate)
        grid.addWidget(self.passphrase_mode, 4, 0, 1, 2)
        group.setLayout(grid)
        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("📋 Copy")
        copy_btn.clicked.connect(self._copy)
        btn_layout.addWidget(copy_btn)
        regen_btn = QPushButton("🔄 Regenerate")
        regen_btn.clicked.connect(self._generate)
        btn_layout.addWidget(regen_btn)
        use_btn = QPushButton("✅ Use This Password")
        use_btn.clicked.connect(self._use)
        btn_layout.addWidget(use_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _generate(self):
        try:
            if self.passphrase_mode.isChecked():
                pwd = generate_passphrase(word_count=4, separator="-")
                self.length_spin.setEnabled(False)
            else:
                self.length_spin.setEnabled(True)
                pwd = generate_password(
                    length=self.length_spin.value(),
                    use_upper=self.upper_check.isChecked(),
                    use_lower=self.lower_check.isChecked(),
                    use_digits=self.digits_check.isChecked(),
                    use_symbols=self.symbols_check.isChecked(),
                    exclude_ambiguous=self.ambiguous_check.isChecked()
                )
            self.preview_edit.setText(pwd)
            strength = estimate_strength(pwd)
            labels = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
            self.strength_label.setText(f"Strength: {labels[strength['score']]} | Crack time: {strength['crack_time']}")
        except Exception as e:
            self.preview_edit.setText("Error: " + str(e))

    def _copy(self):
        pwd = self.preview_edit.text()
        if pwd:
            clipboard = QApplication.clipboard()
            self._old_clipboard = clipboard.text()
            clipboard.setText(pwd)
            if sys.platform.startswith("linux"):
                clipboard.clear(mode=QApplication.clipboard().Mode.Selection)
            self.strength_label.setText("Copied! (auto-clear 30s)")
            self.clipboard_timer.start(30000)

    def _clear_clipboard(self):
        clipboard = QApplication.clipboard()
        if hasattr(self, '_old_clipboard') and clipboard.text() == self.preview_edit.text():
            clipboard.setText(self._old_clipboard)
        else:
            clipboard.clear()
        self.clipboard_timer.stop()
        self.strength_label.setText("Clipboard cleared.")

    def _use(self):
        self.accept()

    def get_password(self) -> str:
        return self.preview_edit.text()