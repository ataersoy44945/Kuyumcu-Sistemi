from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QStackedWidget, QApplication
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from frontend.styles.app_theme import (
    Colors, Fonts,
    gold_button_style, ghost_button_style, input_style,
)


class LoginWindow(QMainWindow):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._setup_window()
        self._build_ui()
        self._center()

    # ── Kurulum ───────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle("Kuyumcu Yönetim Sistemi — Giriş")
        self.setFixedSize(980, 620)
        self.setStyleSheet(f"QMainWindow {{ background: {Colors.BG_DARK}; }}")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_left(), 2)
        layout.addWidget(self._build_right(), 3)

    # ── Sol Panel (Marka) ─────────────────────────────────────

    def _build_left(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {Colors.BG_ELEVATED};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 56, 48, 40)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("💎")
        logo.setFixedSize(80, 80)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            font-size: 42px;
            background: {Colors.GOLD_PRIMARY}22;
            border: 2px solid {Colors.GOLD_PRIMARY};
            border-radius: 40px;
        """)
        layout.addWidget(logo)
        layout.addSpacing(22)

        title = QLabel("Kuyumcu\nYönetim Sistemi")
        title.setStyleSheet(f"""
            color: {Colors.GOLD_PRIMARY};
            font-size: 26px; font-weight: bold;
            font-family: {Fonts.FAMILY_PRIMARY};
        """)
        layout.addWidget(title)
        layout.addSpacing(10)

        tagline = QLabel("Profesyonel Altın & Mücevher\nMağaza Yönetimi")
        tagline.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(tagline)
        layout.addSpacing(40)

        for feat in [
            "Canlı Altın & Döviz Takibi",
            "Ürün ve Stok Yönetimi",
            "Müşteri & Sipariş Takibi",
            "Otomatik Fiyat Hesaplama",
            "Admin & Kullanıcı Paneli",
        ]:
            row = QHBoxLayout()
            dot = QLabel("◆")
            dot.setStyleSheet(f"color: {Colors.GOLD_PRIMARY}; font-size: 9px;")
            txt = QLabel(feat)
            txt.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
            row.addWidget(dot)
            row.addSpacing(8)
            row.addWidget(txt)
            row.addStretch()
            layout.addLayout(row)
            layout.addSpacing(8)

        layout.addStretch()

        ver = QLabel("v1.0.0  ·  Kuyumcu Pro")
        ver.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(ver)
        return panel

    # ── Sağ Panel (Form) ──────────────────────────────────────

    def _build_right(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {Colors.BG_DARK};")
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(64, 40, 64, 40)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_login_form())    # 0
        self._stack.addWidget(self._build_register_form()) # 1
        layout.addStretch()
        layout.addWidget(self._stack)
        layout.addStretch()
        return panel

    # ── Giriş Formu ───────────────────────────────────────────

    def _build_login_form(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._add_form_title(lay, "Giriş Yap", "Hesabınıza erişin")
        lay.addSpacing(28)

        lay.addWidget(self._lbl("Kullanıcı Adı"))
        lay.addSpacing(5)
        self._u_user = self._input("kullanici_adi")
        lay.addWidget(self._u_user)
        lay.addSpacing(14)

        lay.addWidget(self._lbl("Şifre"))
        lay.addSpacing(5)
        self._u_pass = self._input("••••••••", password=True)
        self._u_pass.returnPressed.connect(self._on_login)
        lay.addWidget(self._u_pass)
        lay.addSpacing(18)

        self._login_err = self._error_label()
        lay.addWidget(self._login_err)
        lay.addSpacing(6)

        btn = QPushButton("Giriş Yap")
        btn.setFixedHeight(48)
        btn.setStyleSheet(gold_button_style())
        btn.clicked.connect(self._on_login)
        lay.addWidget(btn)
        lay.addSpacing(18)

        lay.addWidget(self._separator())
        lay.addSpacing(14)

        btn2 = QPushButton("Hesap Oluştur")
        btn2.setFixedHeight(44)
        btn2.setStyleSheet(ghost_button_style())
        btn2.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        lay.addWidget(btn2)

        hint = QLabel("Varsayılan admin: admin / admin123")
        hint.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(12)
        lay.addWidget(hint)
        return w

    # ── Kayıt Formu ───────────────────────────────────────────

    def _build_register_form(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._add_form_title(lay, "Hesap Oluştur", "Yeni müşteri kaydı")
        lay.addSpacing(20)

        row = QHBoxLayout()
        row.setSpacing(12)
        col1, col2 = QVBoxLayout(), QVBoxLayout()
        col1.addWidget(self._lbl("Ad"))
        col1.addSpacing(4)
        self._r_first = self._input("Adınız", h=40)
        col1.addWidget(self._r_first)
        col2.addWidget(self._lbl("Soyad"))
        col2.addSpacing(4)
        self._r_last = self._input("Soyadınız", h=40)
        col2.addWidget(self._r_last)
        row.addLayout(col1)
        row.addLayout(col2)
        lay.addLayout(row)
        lay.addSpacing(10)

        lay.addWidget(self._lbl("Kullanıcı Adı"))
        lay.addSpacing(4)
        self._r_user = self._input("kullanici_adi", h=40)
        lay.addWidget(self._r_user)
        lay.addSpacing(10)

        lay.addWidget(self._lbl("E-posta"))
        lay.addSpacing(4)
        self._r_email = self._input("ornek@email.com", h=40)
        lay.addWidget(self._r_email)
        lay.addSpacing(10)

        lay.addWidget(self._lbl("Şifre (en az 6 karakter)"))
        lay.addSpacing(4)
        self._r_pass = self._input("••••••••", password=True, h=40)
        lay.addWidget(self._r_pass)
        lay.addSpacing(14)

        self._reg_err = self._error_label()
        lay.addWidget(self._reg_err)
        lay.addSpacing(6)

        btn = QPushButton("Kayıt Ol")
        btn.setFixedHeight(44)
        btn.setStyleSheet(gold_button_style())
        btn.clicked.connect(self._on_register)
        lay.addWidget(btn)
        lay.addSpacing(10)

        back = QPushButton("← Giriş ekranına dön")
        back.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {Colors.TEXT_SECONDARY};
                border: none; font-size: 13px; }}
            QPushButton:hover {{ color: {Colors.GOLD_PRIMARY}; }}
        """)
        back.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        lay.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    # ── Yardımcılar ───────────────────────────────────────────

    def _add_form_title(self, layout, title: str, sub: str) -> None:
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 26px; font-weight: bold;")
        layout.addWidget(lbl)
        layout.addSpacing(4)
        s = QLabel(sub)
        s.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px;")
        layout.addWidget(s)

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def _input(self, placeholder: str, password: bool = False, h: int = 44) -> QLineEdit:
        f = QLineEdit()
        f.setPlaceholderText(placeholder)
        f.setFixedHeight(h)
        f.setStyleSheet(input_style())
        if password:
            f.setEchoMode(QLineEdit.EchoMode.Password)
        return f

    def _error_label(self) -> QLabel:
        l = QLabel("")
        l.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.hide()
        return l

    def _separator(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        for _ in range(2):
            f = QFrame()
            f.setFrameShape(QFrame.Shape.HLine)
            f.setStyleSheet(f"color: {Colors.BORDER};")
            lay.addWidget(f)
            if _ == 0:
                l = QLabel("veya")
                l.setStyleSheet(f"color: {Colors.TEXT_MUTED}; padding: 0 10px;")
                lay.addWidget(l)
        return w

    # ── Eylemler ──────────────────────────────────────────────

    def _on_login(self) -> None:
        u = self._u_user.text().strip()
        p = self._u_pass.text()
        if not u or not p:
            self._login_err.setText("Kullanıcı adı ve şifre gereklidir.")
            self._login_err.show()
            return
        user = self._ctx.auth_service.login(u, p)
        if user is None:
            self._login_err.setText("Kullanıcı adı veya şifre hatalı.")
            self._login_err.show()
            return
        self._open_panel(user)

    def _on_register(self) -> None:
        from backend.utils.validators import ValidationError
        try:
            user = self._ctx.auth_service.register(
                username=self._r_user.text(),
                email=self._r_email.text(),
                password=self._r_pass.text(),
                first_name=self._r_first.text(),
                last_name=self._r_last.text(),
            )
            self._ctx.auth_service._current_user = user
            self._open_panel(user)
        except (ValidationError, ValueError) as e:
            self._reg_err.setText(str(e))
            self._reg_err.show()

    def _open_panel(self, user) -> None:
        if user.is_admin():
            from frontend.windows.admin_window import AdminWindow
            win = AdminWindow(self._ctx)
        else:
            from frontend.windows.user_window import UserWindow
            win = UserWindow(self._ctx)
        win.show()
        self.close()

    def _center(self) -> None:
        geo = QApplication.primaryScreen().geometry()
        self.move((geo.width() - self.width()) // 2, (geo.height() - self.height()) // 2)
