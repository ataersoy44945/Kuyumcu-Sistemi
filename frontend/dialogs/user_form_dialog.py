"""
UserFormDialog — admin panelinden yeni kullanıcı ekleme formu.

Alanlar: Ad · Soyad · Kullanıcı adı · E-posta · Telefon · Rol · Şifre · Aktif
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Radius, gold_btn, input_field


class UserFormDialog(QDialog):
    """Yeni kullanıcı eklemek için modal form."""

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self.created_user = None    # başarı durumunda oluşturulan kullanıcı
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle("Yeni Kullanıcı")
        self.setModal(True)
        self.setFixedSize(520, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        # Başlık
        title = QLabel("👤  Yeni Kullanıcı Oluştur")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; border: none;"
        )
        sub = QLabel("Müşteri veya yönetici hesabı ekleyin")
        sub.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        lay.addWidget(title)
        lay.addWidget(sub)
        lay.addSpacing(4)

        # Form
        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        def add_field(row: int, col: int, label: str, widget) -> None:
            lbl = QLabel(label.upper())
            lbl.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                f"letter-spacing: 0.6px; border: none;"
            )
            form.addWidget(lbl, row * 2,     col)
            form.addWidget(widget, row * 2 + 1, col)

        self._first_name = self._line_edit("örn. Ayşe")
        self._last_name  = self._line_edit("örn. Yılmaz")
        self._username   = self._line_edit("en az 3 karakter, küçük harf")
        self._email      = self._line_edit("ornek@mail.com")
        self._phone      = self._line_edit("(opsiyonel)")
        self._password   = self._line_edit("en az 4 karakter")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)

        self._role_cb = QComboBox()
        self._role_cb.setFixedHeight(38)
        self._role_cb.setStyleSheet(input_field())
        self._role_cb.addItem("Müşteri",  "customer")
        self._role_cb.addItem("Yönetici", "admin")

        self._active_cb = QCheckBox("  Hesap aktif")
        self._active_cb.setChecked(True)
        self._active_cb.setStyleSheet(f"""
            QCheckBox {{ color: {Colors.TEXT_BODY}; font-size: 12px; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 4px;
                background: {Colors.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.GOLD};
                border-color: {Colors.GOLD};
            }}
        """)

        add_field(0, 0, "Ad",            self._first_name)
        add_field(0, 1, "Soyad",         self._last_name)
        add_field(1, 0, "Kullanıcı Adı", self._username)
        add_field(1, 1, "E-posta",       self._email)
        add_field(2, 0, "Telefon",       self._phone)
        add_field(2, 1, "Rol",           self._role_cb)
        add_field(3, 0, "Şifre",         self._password)
        form.addWidget(self._active_cb, 7, 1)

        lay.addLayout(form)

        # Hata etiketi
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

        btn_save = QPushButton("Kullanıcıyı Oluştur")
        btn_save.setFixedSize(170, 40)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet(gold_btn())
        btn_save.clicked.connect(self._submit)
        btn_row.addWidget(btn_save)

        lay.addLayout(btn_row)

    def _line_edit(self, placeholder: str) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(38)
        le.setStyleSheet(input_field())
        return le

    # ── Submit ────────────────────────────────────────────────

    def _submit(self) -> None:
        try:
            user = self._ctx.auth_service.admin_create_user(
                username   = self._username.text(),
                email      = self._email.text(),
                password   = self._password.text(),
                first_name = self._first_name.text(),
                last_name  = self._last_name.text(),
                phone      = self._phone.text() or None,
                role       = self._role_cb.currentData(),
                is_active  = self._active_cb.isChecked(),
            )
            self.created_user = user
            self.accept()
        except (ValueError, RuntimeError) as e:
            self._error_lbl.setText(f"⚠  {e}")
