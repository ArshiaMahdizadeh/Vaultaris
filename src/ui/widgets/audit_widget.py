from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.core.vault_manager import VaultManager
from src.core.audit import analyze_vault, check_password_breach


class BreachCheckThread(QThread):
    result = pyqtSignal(int)
    error  = pyqtSignal(str)

    def __init__(self, passwords):
        super().__init__()
        self.passwords = passwords

    def run(self):
        breached = 0
        for pwd in self.passwords:
            count = check_password_breach(pwd)
            if count < 0:
                self.error.emit("Network error or API limit reached.")
                return
            if count > 0:
                breached += 1
        self.result.emit(breached)


class StatCard(QFrame):
    def __init__(self, label: str, value: str, color: str = "#4f8ef7", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #13131e;
                border: 1px solid #2c2c42;
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700; background: transparent;")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #6666888; font-size: 11px; font-weight: 600; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def set_value(self, value: str):
        self.value_lbl.setText(value)


class AuditWidget(QWidget):
    def __init__(self, manager: VaultManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.breach_count = 0
        self._init_ui()
        self._run_analysis()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(16)

        # ── Header ──
        hdr = QHBoxLayout()
        title = QLabel("Security Audit")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #dde1f0;")
        hdr.addWidget(title)
        hdr.addStretch()

        self.breach_btn = QPushButton("Check Breaches (HIBP)")
        self.breach_btn.setFixedHeight(36)
        self.breach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.breach_btn.clicked.connect(self._run_breach_check)
        hdr.addWidget(self.breach_btn)

        root.addLayout(hdr)

        # ── Health score bar ──
        score_frame = QFrame()
        score_frame.setStyleSheet("""
            QFrame {
                background-color: #13131e;
                border: 1px solid #2c2c42;
                border-radius: 10px;
            }
        """)
        score_layout = QVBoxLayout(score_frame)
        score_layout.setContentsMargins(20, 16, 20, 16)
        score_layout.setSpacing(8)

        score_hdr = QHBoxLayout()
        score_lbl = QLabel("Vault Health Score")
        score_lbl.setStyleSheet("color: #dde1f0; font-size: 13px; font-weight: 600; background: transparent;")
        score_hdr.addWidget(score_lbl)
        score_hdr.addStretch()
        self.score_pct = QLabel("--")
        self.score_pct.setStyleSheet("color: #4f8ef7; font-size: 20px; font-weight: 700; background: transparent;")
        score_hdr.addWidget(self.score_pct)
        score_layout.addLayout(score_hdr)

        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setTextVisible(False)
        self.score_bar.setFixedHeight(8)
        score_layout.addWidget(self.score_bar)

        root.addWidget(score_frame)

        # ── Stat cards ──
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.card_total   = StatCard("Total Items",  "0", "#4f8ef7")
        self.card_weak    = StatCard("Weak",          "0", "#f05c5c")
        self.card_reused  = StatCard("Reused",        "0", "#f5a623")
        self.card_old     = StatCard("Old (>90d)",    "0", "#8888aa")
        self.card_breach  = StatCard("Breached",      "0", "#f05c5c")
        for c in [self.card_total, self.card_weak, self.card_reused, self.card_old, self.card_breach]:
            cards_row.addWidget(c)
        root.addLayout(cards_row)

        # ── Issues list ──
        issues_lbl = QLabel("Issues Found")
        issues_lbl.setStyleSheet("color: #8888aa; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        root.addWidget(issues_lbl)

        self.issues_list = QListWidget()
        root.addWidget(self.issues_list, stretch=1)

    def _run_analysis(self):
        try:
            items = self.manager.get_items() if self.manager.active_vault else []
        except RuntimeError:
            self.score_pct.setText("--")
            return

        result = analyze_vault(items)
        score = result["health_score"]

        self.score_bar.setValue(score)
        self.score_pct.setText(f"{score}%")

        if score >= 80:
            color = "#3ecf8e"
        elif score >= 50:
            color = "#f5a623"
        else:
            color = "#f05c5c"
        self.score_bar.setStyleSheet(f"""
            QProgressBar {{ background: #2c2c42; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}
        """)
        self.score_pct.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 700; background: transparent;")

        self.card_total.set_value(str(result["total_items"]))
        self.card_weak.set_value(str(result["weak_count"]))
        self.card_reused.set_value(str(result["reused_count"]))
        self.card_old.set_value(str(result["old_count"]))
        self.card_breach.set_value(str(self.breach_count))

        self.issues_list.clear()
        for detail in result["details"]:
            issues_text = "  ·  ".join(detail["issues"])
            text = f"{detail['title']}"
            if detail["username"]:
                text += f"  ({detail['username']})"
            text += f"  —  {issues_text}"
            li = QListWidgetItem(text)
            li.setForeground(Qt.GlobalColor.white)
            self.issues_list.addItem(li)

        if not result["details"]:
            li = QListWidgetItem("No issues found — great job!")
            li.setForeground(Qt.GlobalColor.green)
            self.issues_list.addItem(li)

    def _run_breach_check(self):
        self.breach_btn.setEnabled(False)
        self.breach_btn.setText("Checking…")
        try:
            items = self.manager.get_items() if self.manager.active_vault else []
        except RuntimeError:
            self.breach_btn.setEnabled(True)
            self.breach_btn.setText("Check Breaches (HIBP)")
            QMessageBox.warning(self, "Locked", "Vault is locked.")
            return
        passwords = [it.password for it in items if it.password]
        if not passwords:
            self.breach_btn.setEnabled(True)
            self.breach_btn.setText("Check Breaches (HIBP)")
            QMessageBox.information(self, "No Passwords", "No password items to check.")
            return
        self.thread = BreachCheckThread(passwords)
        self.thread.result.connect(self._on_breach_done)
        self.thread.error.connect(self._on_breach_error)
        self.thread.start()

    def _on_breach_done(self, count):
        self.breach_count = count
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("Check Breaches (HIBP)")
        self._run_analysis()
        if count:
            QMessageBox.warning(self, "Breach Check",
                f"{count} password(s) found in known data breaches.\nChange them immediately.")
        else:
            QMessageBox.information(self, "Breach Check", "No breached passwords found.")

    def _on_breach_error(self, msg):
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("Check Breaches (HIBP)")
        QMessageBox.warning(self, "Error", msg)
