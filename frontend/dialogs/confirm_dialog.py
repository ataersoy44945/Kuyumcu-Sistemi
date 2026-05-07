from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from frontend.styles.app_theme import Colors, Radius


class ConfirmDialog(QDialog):

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Radius.LG};
            }}
        """)
        self._build_ui(title, message)

    def _build_ui(self, title: str, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 17px; font-weight: bold;")
        layout.addWidget(lbl_title)

        lbl_msg = QLabel(message)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(lbl_msg)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_cancel = QPushButton("İptal")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER}; border-radius: {Radius.SM};
                font-size: 13px; padding: 0 20px;
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD_PRIMARY}; color: {Colors.GOLD_PRIMARY}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Evet, Devam Et")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ERROR}; color: white;
                border: none; border-radius: {Radius.SM};
                font-size: 13px; font-weight: bold; padding: 0 20px;
            }}
            QPushButton:hover {{ background: #c62828; }}
        """)
        btn_ok.clicked.connect(self.accept)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    @staticmethod
    def ask(parent, title: str, message: str) -> bool:
        dlg = ConfirmDialog(title, message, parent)
        return dlg.exec() == QDialog.DialogCode.Accepted
