from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Fonts, Radius


# ── Arka plan thread: kur verisini UI dondurmadan çeker ───────

class _RateWorker(QThread):
    fetched = pyqtSignal(object)   # dict: {rates, btc_usd}

    def __init__(self, svc, api):
        super().__init__()
        self._svc = svc
        self._api = api

    def run(self):
        data = self._svc.refresh()
        btc_usd = None
        try:
            raw = self._api.fetch_btc()
            if raw and "price" in raw:
                btc_usd = float(raw["price"])
        except Exception:
            pass
        self.fetched.emit({"rates": data, "btc_usd": btc_usd})


# ── Topbar'daki küçük piyasa veri chip'i ──────────────────────

class _MarketChip(QFrame):
    def __init__(self, ticker: str, icon: str, color: str, bg: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(134, 56)
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {color}50;
                border-radius: {Radius.MD};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 7, 10, 7)
        lay.setSpacing(2)

        ticker_lbl = QLabel(f"{icon}  {ticker}")
        ticker_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            f"background: transparent; border: none; letter-spacing: 0.3px;"
        )
        self._val_lbl = QLabel("—")
        self._val_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(ticker_lbl)
        lay.addWidget(self._val_lbl)

    def set_value(self, text: str) -> None:
        self._val_lbl.setText(text)


# ── Ana pencere ───────────────────────────────────────────────

class AdminWindow(QMainWindow):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx        = ctx
        self._user       = ctx.auth_service.get_current_user()
        self._rate_worker = None
        self._nav_items  = [
            ("📊", "Dashboard",     0),
            ("📦", "Ürünler",       1),
            ("🏷️",  "Kategoriler",  2),
            ("👥", "Kullanıcılar",  3),
            ("📋", "Siparişler",    4),
            ("💱", "Döviz Kurları", 5),
        ]
        self._setup_window()
        self._build_ui()
        self._go(0)
        self._start_rate_timer()

    # ── Kurulum ───────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle(f"Kuyumcu Pro — {self._user.full_name()}")
        self.setMinimumSize(1280, 780)
        self.showMaximized()
        self.setStyleSheet(f"QMainWindow {{ background: {Colors.BG_BASE}; }}")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)

    # ── Sidebar ───────────────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(256)
        sidebar.setStyleSheet(
            f"QWidget {{ background: {Colors.BG_RAISED}; }}"
            f"QWidget > QFrame {{ border-right: 1px solid {Colors.BORDER_DEFAULT}; }}"
        )
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_logo())
        lay.addSpacing(8)
        lay.addWidget(self._build_nav_section())
        lay.addStretch()
        lay.addWidget(self._build_user_area())
        return sidebar

    def _build_logo(self) -> QWidget:
        logo = QWidget()
        logo.setFixedHeight(88)
        logo.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {Colors.BG_ELEVATED}, stop:1 {Colors.BG_RAISED});
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(logo)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(12)

        ico = QLabel("💎")
        ico.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        ico.setFixedWidth(36)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        brand = QLabel("Kuyumcu Pro")
        brand.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        sub = QLabel("Yönetim Paneli")
        sub.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; "
            f"background: transparent; border: none; letter-spacing: 0.5px;"
        )
        text_col.addWidget(brand)
        text_col.addWidget(sub)

        lay.addWidget(ico)
        lay.addLayout(text_col)
        lay.addStretch()
        return logo

    def _build_nav_section(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(2)

        section_lbl = QLabel("  YÖNETİM")
        section_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1.2px; padding: 0 20px 6px; background: transparent;"
        )
        lay.addWidget(section_lbl)

        self._nav_buttons: list[QPushButton] = []
        for icon, label, idx in self._nav_items:
            btn = self._make_nav_btn(icon, label, idx)
            lay.addWidget(btn)
            self._nav_buttons.append(btn)

        return w

    def _make_nav_btn(self, icon: str, label: str, idx: int) -> QPushButton:
        btn = QPushButton(f"  {icon}    {label}")
        btn.setFixedHeight(50)
        btn.setStyleSheet(self._nav_style(False))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _, i=idx: self._go(i))
        return btn

    def _nav_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(212,175,55,0.14), stop:1 rgba(212,175,55,0.03));
                    color: {Colors.GOLD};
                    border: none;
                    border-left: 3px solid {Colors.GOLD};
                    text-align: left;
                    padding-left: 17px;
                    font-size: 14px;
                    font-weight: 600;
                    font-family: {Fonts.FAMILY};
                }}
            """
        return f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_MUTED};
                border: none;
                border-left: 3px solid transparent;
                text-align: left;
                padding-left: 17px;
                font-size: 14px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(212,175,55,0.05);
                color: {Colors.TEXT_BODY};
                border-left: 3px solid {Colors.BORDER_BRIGHT};
            }}
        """

    def _build_user_area(self) -> QWidget:
        frame = QWidget()
        frame.setStyleSheet(
            f"QWidget {{ border-top: 1px solid {Colors.BORDER_DEFAULT}; "
            f"background: {Colors.BG_RAISED}; }}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # Avatar + isim satırı
        row = QHBoxLayout()
        row.setSpacing(10)

        # İnitial avatar
        parts   = self._user.full_name().split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        avatar  = QLabel(initials)
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD_DIM});
            color: {Colors.TEXT_ON_GOLD};
            border-radius: 19px;
            font-size: 14px; font-weight: 800;
            border: none;
        """)

        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(self._user.full_name())
        name_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600; border: none;"
        )
        role_lbl = QLabel(self._user.display_role())
        role_lbl.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 10px; letter-spacing: 0.3px; border: none;"
        )
        info.addWidget(name_lbl)
        info.addWidget(role_lbl)

        row.addWidget(avatar)
        row.addLayout(info)
        row.addStretch()
        lay.addLayout(row)

        btn_logout = QPushButton("  ⎋  Çıkış Yap")
        btn_logout.setFixedHeight(34)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.RED};
                border: 1px solid {Colors.RED}44; border-radius: {Radius.SM};
                font-size: 12px; text-align: left; padding-left: 10px;
            }}
            QPushButton:hover {{
                background: {Colors.RED_BG}; border-color: {Colors.RED};
            }}
        """)
        btn_logout.clicked.connect(self._logout)
        lay.addWidget(btn_logout)
        return frame

    # ── Content alanı ─────────────────────────────────────────

    def _build_content(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {Colors.BG_BASE};")
        self._add_pages()
        lay.addWidget(self._stack)
        return w

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(72)
        bar.setStyleSheet(f"""
            QWidget {{
                background: {Colors.BG_RAISED};
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(28, 0, 24, 0)
        lay.setSpacing(0)

        self._page_title = QLabel("Dashboard")
        self._page_title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(self._page_title)
        lay.addStretch()

        # 4 market chip
        self._chip_usd = _MarketChip("USD / TRY", "💵", Colors.BLUE,  Colors.BLUE_BG)
        self._chip_eur = _MarketChip("EUR / TRY", "💶", Colors.GREEN, Colors.GREEN_BG)
        self._chip_au  = _MarketChip("Gram Altın", "🪙", Colors.GOLD,  Colors.GOLD_SUBTLE)
        self._chip_btc = _MarketChip("BTC / USD",  "₿",  Colors.BTC,  Colors.BTC_BG)

        for chip in (self._chip_usd, self._chip_eur, self._chip_au, self._chip_btc):
            lay.addWidget(chip)
            lay.addSpacing(8)

        self._lbl_update = QLabel("Yükleniyor…")
        self._lbl_update.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; "
            f"background: transparent; border: none;"
        )
        lay.addSpacing(4)
        lay.addWidget(self._lbl_update)
        lay.addSpacing(4)
        return bar

    def _add_pages(self) -> None:
        from frontend.pages.admin.dashboard_page  import DashboardPage
        from frontend.pages.admin.products_page   import ProductsPage
        from frontend.pages.admin.categories_page import CategoriesPage
        from frontend.pages.admin.users_page      import UsersPage
        from frontend.pages.admin.orders_page     import OrdersPage
        from frontend.pages.admin.rates_page      import RatesPage

        self._pages = [
            DashboardPage(self._ctx),
            ProductsPage(self._ctx),
            CategoriesPage(self._ctx),
            UsersPage(self._ctx),
            OrdersPage(self._ctx),
            RatesPage(self._ctx),
        ]
        for p in self._pages:
            self._stack.addWidget(p)

    # ── Navigasyon ────────────────────────────────────────────

    def _go(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self._page_title.setText(self._nav_items[idx][1])
        for i, btn in enumerate(self._nav_buttons):
            btn.setStyleSheet(self._nav_style(i == idx))
        page = self._pages[idx]
        if hasattr(page, "refresh"):
            page.refresh()

    # ── Otomatik kur yenileme (60 sn, worker thread) ─────────

    def _start_rate_timer(self) -> None:
        self._fetch_rates()
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._fetch_rates)
        self._rate_timer.start(60_000)

    def _fetch_rates(self) -> None:
        if self._rate_worker and self._rate_worker.isRunning():
            return
        self._lbl_update.setText("↻  Güncelleniyor…")
        self._rate_worker = _RateWorker(
            self._ctx.exchange_service,
            self._ctx.rate_api,
        )
        self._rate_worker.fetched.connect(self._on_rates_done)
        self._rate_worker.start()

    def _on_rates_done(self, result: dict) -> None:
        rates   = result.get("rates")
        btc_usd = result.get("btc_usd")

        if rates:
            self._chip_usd.set_value(f"₺ {rates.usd_try:,.4f}")
            self._chip_eur.set_value(f"₺ {rates.eur_try:,.4f}")
            self._chip_au.set_value(f"₺ {rates.gold_gram_try:,.2f}")
            self._lbl_update.setText(f"↻  {rates.display_update_time()}")
        else:
            self._lbl_update.setText("⚠  Veri alınamadı")

        if btc_usd:
            self._chip_btc.set_value(f"${btc_usd:,.0f}")
        else:
            self._chip_btc.set_value("—")

    # ── Çıkış ─────────────────────────────────────────────────

    def _logout(self) -> None:
        if self._rate_timer:
            self._rate_timer.stop()
        self._ctx.auth_service.logout()
        from frontend.windows.login_window import LoginWindow
        win = LoginWindow(self._ctx)
        win.show()
        self.close()
