"""
PasswordResetDialog — admin panelinden bir kullanıcının şifresini sıfırlama.

Admin yeni bir şifre yazar (veya rastgele üret butonuyla doldurur), onaylar.
Şifre düz metin olarak hiçbir yerde saklanmaz; AuthService.admin_reset_password
çağrısı ile hashlenip DB'ye yazılır.
"""

import secrets
import string

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication

from backend.app_context import AppContext
from backend.models.user import User
from frontend.styles.app_theme import Colors, Radius, gold_btn, input_field


class PasswordResetDialog(QDialog):

    def __init__(self, ctx: AppContext, user: User, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self._user = user
        self.new_password: str | None = None  # başarı durumunda atanır
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle("Şifre Sıfırla")
        self.setModal(True)
        self.setFixedSize(440, 360)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        title = QLabel("🔑  Şifre Sıfırla")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; border: none;"
        )
        lay.addWidget(title)

        info = QLabel(
            f"<b style='color:{Colors.GOLD};'>{self._user.username}</b> "
            f"({self._user.full_name()}) için yeni bir şifre belirleyin."
        )
        info.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 12px; border: none;"
        )
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addSpacing(4)

        # Şifre alanı + göster/gizle + üret
        lbl = QLabel("YENİ ŞİFRE")
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.6px; border: none;"
        )
        lay.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(8)

        self._pw = QLineEdit()
        self._pw.setPlaceholderText("en az 4 karakter")
        self._pw.setFixedHeight(38)
        self._pw.setStyleSheet(input_field())
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        row.addWidget(self._pw, 1)

        self._toggle_btn = QPushButton("👁")
        self._toggle_btn.setFixedSize(38, 38)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setStyleSheet(self._mini_btn_style())
        self._toggle_btn.toggled.connect(self._toggle_visibility)
        row.addWidget(self._toggle_btn)

        gen_btn = QPushButton("Üret")
        gen_btn.setFixedSize(64, 38)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.setStyleSheet(self._mini_btn_style())
        gen_btn.clicked.connect(self._generate)
        row.addWidget(gen_btn)

        lay.addLayout(row)

        hint = QLabel(
            "İpucu: Şifre kullanıcıya hashlenmeden önce gösterilir; bu pencereyi "
            "kapattıktan sonra düz metin geri alınamaz."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        lay.addWidget(hint)

        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(
            f"color: {Colors.RED}; font-size: 12px; border: none;"
        )
        self._error_lbl.setWordWrap(True)
        lay.addWidget(self._error_lbl)

        lay.addStretch()

        # Butonlar
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.setFixedSize(100, 40)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}; font-size: 13px;
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD}; color: {Colors.GOLD}; }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Şifreyi Sıfırla")
        btn_save.setFixedSize(150, 40)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(gold_btn())
        btn_save.clicked.connect(self._submit)
        btn_row.addWidget(btn_save)

        lay.addLayout(btn_row)

    # ── Yardımcılar ───────────────────────────────────────────

    @staticmethod
    def _mini_btn_style() -> str:
        return f"""
            QPushButton {{
                background: {Colors.BG_INPUT}; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD}; color: {Colors.GOLD}; }}
            QPushButton:checked {{ background: {Colors.GOLD}22; border-color: {Colors.GOLD}; color: {Colors.GOLD}; }}
        """

    def _toggle_visibility(self, on: bool) -> None:
        self._pw.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
        )

    def _generate(self) -> None:
        alphabet = string.ascii_letters + string.digits
        pw = "".join(secrets.choice(alphabet) for _ in range(10))
        self._pw.setText(pw)
        # Üretilen şifreyi panoya da kopyala (admin'in işini kolaylaştır)
        QGuiApplication.clipboard().setText(pw)
        # Panoya kopyalandığını kullanıcıya hissettirmek için göster
        self._toggle_btn.setChecked(True)

    def _submit(self) -> None:
        pw = self._pw.text().strip()
        try:
            ok = self._ctx.auth_service.admin_reset_password(self._user.id, pw)
            if not ok:
                self._error_lbl.setText("⚠  Şifre güncellenemedi.")
                return
            self.new_password = pw
            QGuiApplication.clipboard().setText(pw)
            self.accept()
        except ValueError as e:
            self._error_lbl.setText(f"⚠  {e}")
