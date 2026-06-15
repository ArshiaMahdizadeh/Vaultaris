import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QPushButton, QGroupBox, QGridLayout,
    QApplication, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QBrush, QColor
from src.core.generator import generate_password, generate_passphrase, estimate_strength

STRENGTH_COLORS = ["#f05c5c", "#f5a623", "#f5d623", "#3ecf8e", "#4f8ef7"]
STRENGTH_LABELS = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]


class StrengthBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self.setFixedHeight(6)

    def set_score(self, score: int):
        self._score = max(0, min(4, score))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        gap = 4
        n = 5
        seg_w = (w - gap * (n - 1)) / n
        for i in range(n):
            x = int(i * (seg_w + gap))
            color = QColor(STRENGTH_COLORS[self._score]) if i <= self._score else QColor("#2c2c42")
            p.fillRect(x, 0, int(seg_w), h, QBrush(color))


class GeneratorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._copied = False
        self.clipboard_timer = QTimer()
        self.clipboard_timer.timeout.connect(self._clear_clipboard)
        self._init_ui()
        self._generate()

    def _init_ui(self):
        # Scrollable so it works on small screens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        main = QVBoxLayout(inner)
        main.setContentsMargins(40, 32, 40, 32)
        main.setSpacing(20)

        # ── Header ──
        title = QLabel("Password Generator")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(title)

        sub = QLabel("Cryptographically secure — powered by secrets.choice")
        sub.setStyleSheet("color: #6666888; font-size: 12px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(sub)

        # ── Preview card ──
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #13131e;
                border: 1px solid #2c2c42;
                border-radius: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)

        self.preview_edit = QLineEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 20px;
                font-family: 'Cascadia Code', 'Fira Code', 'Courier New', monospace;
                padding: 8px;
                letter-spacing: 1px;
            }
        """)
        self.preview_edit.setMinimumHeight(54)
        card_layout.addWidget(self.preview_edit)

        # Strength row
        str_row = QHBoxLayout()
        str_row.setSpacing(10)
        self.strength_bar = StrengthBar()
        str_row.addWidget(self.strength_bar, stretch=1)
        self.strength_label = QLabel("--")
        self.strength_label.setStyleSheet("color: #6666888; font-size: 12px; font-weight: 600;")
        self.strength_label.setMinimumWidth(72)
        self.strength_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        str_row.addWidget(self.strength_label)
        card_layout.addLayout(str_row)

        self.crack_label = QLabel("Crack time: --")
        self.crack_label.setStyleSheet("color: #44445a; font-size: 11px;")
        self.crack_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.crack_label)

        main.addWidget(card)

        # ── Action buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setProperty("primary", True)
        self.copy_btn.setStyle(self.copy_btn.style())
        self.copy_btn.setFixedHeight(40)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy)
        btn_row.addWidget(self.copy_btn, stretch=1)

        regen_btn = QPushButton("Regenerate")
        regen_btn.setFixedHeight(40)
        regen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        regen_btn.clicked.connect(self._generate)
        btn_row.addWidget(regen_btn, stretch=1)

        main.addLayout(btn_row)

        # ── Config panel ──
        cfg = QGroupBox("Configuration")
        cfg_layout = QVBoxLayout(cfg)
        cfg_layout.setContentsMargins(16, 8, 16, 16)
        cfg_layout.setSpacing(12)

        # Length row
        len_row = QHBoxLayout()
        len_row.setSpacing(12)
        len_row.addWidget(QLabel("Length"))
        self.length_spin = QSpinBox()
        self.length_spin.setRange(4, 128)
        self.length_spin.setValue(20)
        self.length_spin.setFixedWidth(80)
        self.length_spin.valueChanged.connect(self._generate)
        len_row.addWidget(self.length_spin)
        len_row.addStretch()
        cfg_layout.addLayout(len_row)

        # Character toggles
        grid = QGridLayout()
        grid.setSpacing(8)
        self.upper_check   = self._toggle("A–Z  Uppercase", True)
        self.lower_check   = self._toggle("a–z  Lowercase", True)
        self.digits_check  = self._toggle("0–9  Numbers",   True)
        self.symbols_check = self._toggle("!@#  Symbols",   True)
        self.ambig_check   = self._toggle("Exclude ambiguous  (O 0 I l 1)", True)
        grid.addWidget(self.upper_check,   0, 0)
        grid.addWidget(self.lower_check,   0, 1)
        grid.addWidget(self.digits_check,  1, 0)
        grid.addWidget(self.symbols_check, 1, 1)
        grid.addWidget(self.ambig_check,   2, 0, 1, 2)
        cfg_layout.addLayout(grid)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background: #2c2c42; max-height: 1px;")
        cfg_layout.addWidget(div)

        self.passphrase_check = self._toggle("Passphrase mode  (4 random words)", False)
        self.passphrase_check.stateChanged.connect(self._on_mode_change)
        cfg_layout.addWidget(self.passphrase_check)

        main.addWidget(cfg)
        main.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _toggle(self, text: str, checked: bool) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setCursor(Qt.CursorShape.PointingHandCursor)
        cb.stateChanged.connect(self._generate)
        return cb

    def _on_mode_change(self, state):
        is_phrase = state == Qt.CheckState.Checked.value
        self.length_spin.setEnabled(not is_phrase)
        self._generate()

    def _generate(self):
        try:
            if self.passphrase_check.isChecked():
                pwd = generate_passphrase(word_count=4, separator="-")
            else:
                pwd = generate_password(
                    length=self.length_spin.value(),
                    use_upper=self.upper_check.isChecked(),
                    use_lower=self.lower_check.isChecked(),
                    use_digits=self.digits_check.isChecked(),
                    use_symbols=self.symbols_check.isChecked(),
                    exclude_ambiguous=self.ambig_check.isChecked(),
                )
            self.preview_edit.setText(pwd)
            result = estimate_strength(pwd)
            score = result["score"]
            self.strength_bar.set_score(score)
            self.strength_label.setText(STRENGTH_LABELS[score])
            self.strength_label.setStyleSheet(
                f"color: {STRENGTH_COLORS[score]}; font-size: 12px; font-weight: 600;"
            )
            self.crack_label.setText(f"Crack time: {result['crack_time']}")
            if self._copied:
                self._reset_copy_btn()
        except Exception as e:
            self.preview_edit.setText("Error")
            self.crack_label.setText(str(e))

    def _copy(self):
        pwd = self.preview_edit.text()
        if not pwd or pwd == "Error":
            return
        clipboard = QApplication.clipboard()
        self._old_clipboard = clipboard.text()
        clipboard.setText(pwd)
        if sys.platform.startswith("linux"):
            clipboard.clear(mode=QApplication.clipboard().Mode.Selection)
        self._copied = True
        self.copy_btn.setText("Copied!")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3ecf8e; color: #0e0e16;
                border: none; border-radius: 8px;
                padding: 9px 18px; font-weight: 700;
            }
            QPushButton:hover { background-color: #55dfa0; }
        """)
        self.clipboard_timer.start(30_000)

    def _clear_clipboard(self):
        clipboard = QApplication.clipboard()
        if hasattr(self, '_old_clipboard') and clipboard.text() == self.preview_edit.text():
            clipboard.setText(self._old_clipboard)
        else:
            clipboard.clear()
        self.clipboard_timer.stop()
        self._reset_copy_btn()

    def _reset_copy_btn(self):
        self._copied = False
        self.copy_btn.setText("Copy")
        self.copy_btn.setProperty("primary", True)
        self.copy_btn.setStyle(self.copy_btn.style())
