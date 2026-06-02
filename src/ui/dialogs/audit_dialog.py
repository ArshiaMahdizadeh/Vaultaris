"""
Security Audit dialog – shows vault health and breach scan results.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from src.core.audit import analyze_vault, check_password_breach
from src.core.vault import Vault

class BreachCheckThread(QThread):
    """Worker thread to avoid freezing UI during HIBP checks."""
    result = pyqtSignal(int)  # count of breached passwords
    error = pyqtSignal(str)

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


class AuditDialog(QDialog):
    def __init__(self, vault: Vault, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.items = vault.get_items()
        self.breach_count = 0
        self.setWindowTitle("Security Audit")
        self.setMinimumSize(500, 450)
        self.setStyleSheet(self._style())
        self._init_ui()
        self._run_analysis()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("🛡️ Security Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Health score bar
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setTextVisible(True)
        layout.addWidget(self.score_bar)

        # Summary labels
        self.summary_label = QLabel("")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary_label)

        # Issues list
        self.issues_list = QListWidget()
        layout.addWidget(self.issues_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.breach_btn = QPushButton("🔍 Check for Breaches")
        self.breach_btn.clicked.connect(self._run_breach_check)
        btn_layout.addWidget(self.breach_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _run_analysis(self):
        """Perform local audit and update UI."""
        result = analyze_vault(self.items)
        score = result["health_score"]
        self.score_bar.setValue(score)
        # Color the progress bar based on score
        if score >= 80:
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #2ecc71; }")
        elif score >= 50:
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #f1c40f; }")
        else:
            self.score_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")

        self.summary_label.setText(
            f"Total items: {result['total_items']}  |  "
            f"Weak: {result['weak_count']}  |  "
            f"Reused: {result['reused_count']}  |  "
            f"Old: {result['old_count']}  |  "
            f"Breached: {self.breach_count}"
        )

        self.issues_list.clear()
        for detail in result["details"]:
            issues_text = ", ".join(detail["issues"])
            item_text = f"{detail['title']} ({detail['username']}) – {issues_text}"
            self.issues_list.addItem(QListWidgetItem(item_text))

    def _run_breach_check(self):
        """Start HIBP check in background thread."""
        self.breach_btn.setEnabled(False)
        self.breach_btn.setText("Checking...")

        passwords = [item.password for item in self.items]
        self.thread = BreachCheckThread(passwords)
        self.thread.result.connect(self._on_breach_done)
        self.thread.error.connect(self._on_breach_error)
        self.thread.start()

    def _on_breach_done(self, breach_count):
        self.breach_count = breach_count
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("🔍 Check for Breaches")
        self._run_analysis()  # refresh summary
        QMessageBox.information(
            self,
            "Breach Check Complete",
            f"{breach_count} password(s) found in known data breaches.\n"
            "Consider changing them immediately."
        )

    def _on_breach_error(self, msg):
        self.breach_btn.setEnabled(True)
        self.breach_btn.setText("🔍 Check for Breaches")
        QMessageBox.warning(self, "Breach Check Failed", msg)

    def _style(self):
        return """
        QDialog {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:1 #16213e);
            border-radius: 16px;
            color: #e0e0e0;
        }
        QLabel {
            color: #e0e0e0;
        }
        QListWidget {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: white;
        }
        QProgressBar {
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            text-align: center;
            color: white;
            background: rgba(0,0,0,0.3);
        }
        QPushButton {
            background: #0f9bff;
            border: none;
            border-radius: 8px;
            color: white;
            padding: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background: #0091ea;
        }
        QPushButton:disabled {
            background: #555;
        }
        """