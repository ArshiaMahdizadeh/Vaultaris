from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QFrame,
    QInputDialog, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from src.core.vault_manager import VaultManager
from src.core.audit import analyze_vault, check_passwords_breach_batch


class BreachCheckThread(QThread):
    result = pyqtSignal(dict)
    error  = pyqtSignal(str)

    def __init__(self, items):
        super().__init__()
        self.items = items

    def run(self):
        passwords = [it.password for it in self.items if it.password]
        if not passwords:
            self.result.emit({})
            return
        counts = check_passwords_breach_batch(passwords)
        breach_details = {}
        pw_idx = 0
        for idx, it in enumerate(self.items):
            if it.password:
                if pw_idx < len(counts):
                    c = counts[pw_idx]
                    if c < 0:
                        self.error.emit("Network error or API limit reached.")
                        return
                    if c > 0:
                        breach_details[idx] = c
                pw_idx += 1
        self.result.emit(breach_details)


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
        self.breach_details = {}
        self._init_ui()

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

        # ── Issues table ──
        issues_lbl = QLabel("Issues Found")
        issues_lbl.setStyleSheet("color: #8888aa; font-size: 11px; font-weight: 600; letter-spacing: 1px;")
        root.addWidget(issues_lbl)

        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(3)
        self.issues_table.setHorizontalHeaderLabels(["Item", "Issues", "Breaches"])
        self.issues_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.issues_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.issues_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.issues_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.issues_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        root.addWidget(self.issues_table, stretch=1)

    def _mask_username(self, username: str) -> str:
        if not username or len(username) <= 2:
            return username or ""
        return username[0] + "*" * (len(username) - 2) + username[-1]

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

        self.issues_table.setRowCount(0)
        for detail in result["details"]:
            issues_text = "  ·  ".join(detail["issues"])
            masked_user = self._mask_username(detail.get("username", ""))
            title_text = detail["title"]
            if masked_user:
                title_text += f"  ({masked_user})"
            breach_count = self.breach_details.get(detail.get("index", -1), 0)
            row = self.issues_table.rowCount()
            self.issues_table.insertRow(row)
            self.issues_table.setItem(row, 0, QTableWidgetItem(title_text))
            self.issues_table.setItem(row, 1, QTableWidgetItem(issues_text))
            self.issues_table.setItem(row, 2, QTableWidgetItem(str(breach_count) if breach_count else ""))

        if not result["details"]:
            self.issues_table.setRowCount(1)
            self.issues_table.setSpan(0, 0, 1, 3)
            self.issues_table.setItem(0, 0, QTableWidgetItem("No issues found — great job!"))

    def _run_breach_check(self):
        self.breach_btn.setEnabled(False)
        self.breach_btn.setText("Checking...")
        try:
            items = self.manager.get_items() if self.manager.active_vault else []
        except RuntimeError:
            self.breach_btn.setEnabled(True)
            self.breach_btn.setText("Check Breaches (HIBP)")
            QMessageBox.warning(self, "Locked", "Vault is locked.")
            return

        # Re-auth dialog
        password, ok = QInputDialog.getText(
            self, "Re-authenticate", "Enter master password to run breach check:",
            echo=QLineEdit.EchoMode.Password
        )
        if not ok or not password:
            self.breach_btn.setEnabled(True)
            self.breach_btn.setText("Check Breaches (HIBP)")
            return

        has_passwords = any(it.password for it in items)
        if not has_passwords:
            self.breach_btn.setEnabled(True)
            self.breach_btn.setText("Check Breaches (HIBP)")
            QMessageBox.information(self, "No Passwords", "No password items to check.")
            return
        self.thread = BreachCheckThread(items)
        self.thread.result.connect(self._on_breach_done)
        self.thread.error.connect(self._on_breach_error)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_breach_done(self, breach_details: dict):
        self.breach_details = breach_details
        self.breach_count = len(breach_details)
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("Check Breaches (HIBP)")
        self._run_analysis()
        if self.breach_count:
            QMessageBox.warning(self, "Breach Check",
                f"{self.breach_count} password(s) found in known data breaches.\nChange them immediately.")
        else:
            QMessageBox.information(self, "Breach Check", "No breached passwords found.")

    def _on_breach_error(self, msg):
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("Check Breaches (HIBP)")
        QMessageBox.warning(self, "Error", msg)

    def closeEvent(self, event):
        if hasattr(self, "thread") and self.thread is not None:
            self.thread.quit()
            self.thread.wait(2000)
        event.accept()
