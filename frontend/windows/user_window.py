from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Fonts, Radius
from frontend.components.cart_bar import CartBar
from frontend.dialogs.order_success_dialog import OrderSuccessDialog


# ── Arka plan thread: kur + BTC verisini UI dondurmadan çeker ─

class _RateWorker(QThread):
    fetched = pyqtSignal(object)   # dict: {rates, btc_usd}

    def __init__(self, svc, api):
        super().__init__()
        self._svc = svc
        self._api = api

    def run(self):
        data    = self._svc.refresh()
        btc_usd = None
        try:
            raw = self._api.fetch_btc()
            if raw and "price" in raw:
                btc_usd = float(raw["price"])
        except Exception:
            pass
        self.fetched.emit({"rates": data, "btc_usd": btc_usd})


# ── Ana pencere ───────────────────────────────────────────────

class UserWindow(QMainWindow):

    # Kenar çubuğu öğeleri — (ikon, etiket, sayfa_indeksi)
    _NAV_ITEMS = [
        ("🏠", "Ana Sayfa",       0),
        ("💎", "Ürünler",         1),
        ("✨", "Koleksiyonlar",   1),
        ("🏷️",  "Kategoriler",   6),
        ("❤️",  "Favorilerim",   2),
        ("🛒", "Sepetim",         3),
        ("📋", "Siparişlerim",    7),
        ("📊", "Altın Fiyatları", 0),
        ("🎁", "Kampanyalar",     5),
    ]

    # Stack içindeki sabit indeksler — kod içinde referans verilen sayfalar
    PAGE_CART       = 3
    PAGE_CAMPAIGNS  = 5
    PAGE_CATEGORIES = 6
    PAGE_ORDERS     = 7
    PAGE_CHECKOUT   = 8

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx         = ctx
        self._user        = ctx.auth_service.get_current_user()
        self._rate_worker = None

        self._setup_window()
        self._build_ui()
        self._go_label("Ana Sayfa", 0)
        self._start_rate_timer()

    # ── Genel kurulum ─────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle(f"Kuyumcu — {self._user.full_name()}")
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
        root.addWidget(self._build_content_area(), 1)

    # ── SOL KENAR ÇUBUĞU ──────────────────────────────────────

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background: {Colors.BG_RAISED};
                border-right: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar_logo())
        lay.addSpacing(6)
        lay.addWidget(self._sidebar_nav())
        lay.addStretch()
        lay.addWidget(self._sidebar_user())
        return sidebar

    def _sidebar_logo(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(88)
        w.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {Colors.BG_ELEVATED}, stop:1 {Colors.BG_RAISED});
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(12)

        gem = QLabel("💎")
        gem.setStyleSheet("font-size: 30px; background: transparent; border: none;")
        gem.setFixedWidth(38)

        col = QVBoxLayout()
        col.setSpacing(2)
        brand = QLabel("Kuyumcu")
        brand.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 17px; font-weight: 700; "
            f"background: transparent; border: none; letter-spacing: 0.5px;"
        )
        sub = QLabel("PREMIUM TAKICILIK")
        sub.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 8px; font-weight: 600; "
            f"letter-spacing: 1.2px; background: transparent; border: none;"
        )
        col.addWidget(brand)
        col.addWidget(sub)

        lay.addWidget(gem)
        lay.addLayout(col)
        lay.addStretch()
        return w

    def _sidebar_nav(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(1)

        section = QLabel("  MAĞAZA")
        section.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1.2px; padding: 0 20px 8px; background: transparent;"
        )
        lay.addWidget(section)

        self._nav_buttons: list[QPushButton] = []
        for icon, label, idx in self._NAV_ITEMS:
            btn = QPushButton(f"  {icon}    {label}")
            btn.setFixedHeight(46)
            btn.setStyleSheet(self._nav_style(False))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx, lbl=label: self._go_label(lbl, i))
            self._nav_buttons.append(btn)
            lay.addWidget(btn)
        return w

    def _sidebar_user(self) -> QWidget:
        frame = QWidget()
        frame.setStyleSheet(
            f"QWidget {{ border-top: 1px solid {Colors.BORDER_DEFAULT}; "
            f"background: {Colors.BG_RAISED}; }}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)

        parts    = self._user.full_name().split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        avatar   = QLabel(initials)
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD_DIM});
            color: {Colors.TEXT_ON_GOLD}; border-radius: 18px;
            font-size: 13px; font-weight: 800; border: none;
        """)

        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(self._user.full_name())
        name_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 12px; font-weight: 600; border: none;"
        )
        role_lbl = QLabel("Müşteri")
        role_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; border: none;"
        )
        info.addWidget(name_lbl)
        info.addWidget(role_lbl)

        row.addWidget(avatar)
        row.addLayout(info)
        row.addStretch()
        lay.addLayout(row)

        btn = QPushButton("  ⎋  Çıkış Yap")
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.RED};
                border: 1px solid {Colors.RED}44; border-radius: {Radius.SM};
                font-size: 11px; text-align: left; padding-left: 10px;
            }}
            QPushButton:hover {{ background: {Colors.RED_BG}; border-color: {Colors.RED}; }}
        """)
        btn.clicked.connect(self._logout)
        lay.addWidget(btn)
        return frame

    def _nav_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(212,175,55,0.14), stop:1 rgba(212,175,55,0.03));
                    color: {Colors.GOLD};
                    border: none; border-left: 3px solid {Colors.GOLD};
                    text-align: left; padding-left: 17px;
                    font-size: 13px; font-weight: 600; font-family: {Fonts.FAMILY};
                }}
            """
        return f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_MUTED};
                border: none; border-left: 3px solid transparent;
                text-align: left; padding-left: 17px;
                font-size: 13px; font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                background: rgba(212,175,55,0.05); color: {Colors.TEXT_BODY};
                border-left: 3px solid {Colors.BORDER_BRIGHT};
            }}
        """

    # ── ÜSTTE BAR + STACK ─────────────────────────────────────

    def _build_content_area(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._build_topbar())
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {Colors.BG_BASE};")
        self._add_pages()
        lay.addWidget(self._stack, 1)

        # Sticky alt sepet barı — sadece sepette ürün varsa görünür.
        self._cart_bar = CartBar()
        self._cart_bar.view_cart_clicked.connect(
            lambda: self._go_label("Sepetim", self.PAGE_CART)
        )
        lay.addWidget(self._cart_bar)
        return w

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setStyleSheet(f"""
            QWidget {{
                background: {Colors.BG_RAISED};
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(10)

        # Sol: hızlı erişim ikonları
        for icon, tip, idx in [("❤️", "Favorilerim", 2), ("🛒", "Sepetim", 3)]:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: 1px solid {Colors.BORDER_DEFAULT};
                    border-radius: 18px; font-size: 16px;
                }}
                QPushButton:hover {{
                    background: {Colors.GOLD_SUBTLE}; border-color: {Colors.GOLD};
                }}
            """)
            btn.clicked.connect(lambda _, i=idx: self._go_idx(i))
            lay.addWidget(btn)

        lay.addStretch()

        # Orta: arama kutusu
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Ürün, koleksiyon, kategori ara…")
        self._search.setFixedSize(340, 38)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.BG_INPUT}; color: {Colors.TEXT_H1};
                border: 1px solid {Colors.BORDER_DEFAULT}; border-radius: 19px;
                padding: 0 18px; font-size: 13px; font-family: {Fonts.FAMILY};
            }}
            QLineEdit:focus {{
                border: 1px solid {Colors.GOLD}; background: {Colors.BG_ELEVATED};
            }}
            QLineEdit::placeholder {{ color: {Colors.TEXT_MUTED}; }}
        """)
        self._search.returnPressed.connect(self._on_search)
        lay.addWidget(self._search)

        lay.addStretch()

        # Sağ: bildirim + kullanıcı
        bell = QPushButton("🔔")
        bell.setFixedSize(36, 36)
        bell.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 18px; font-size: 15px;
            }}
            QPushButton:hover {{ background: {Colors.GOLD_SUBTLE}; border-color: {Colors.GOLD}; }}
        """)
        lay.addWidget(bell)
        lay.addSpacing(6)

        parts    = self._user.full_name().split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        avatar   = QLabel(initials)
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD_DIM});
            color: {Colors.TEXT_ON_GOLD}; border-radius: 17px;
            font-size: 12px; font-weight: 800; border: none;
        """)
        lay.addWidget(avatar)
        lay.addSpacing(6)

        name_lbl = QLabel(self._user.first_name)
        name_lbl.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 13px; border: none;"
        )
        lay.addWidget(name_lbl)
        return bar

    def _add_pages(self) -> None:
        from frontend.pages.user.home_page       import HomePage
        from frontend.pages.user.catalog_page    import CatalogPage
        from frontend.pages.user.favorites_page  import FavoritesPage
        from frontend.pages.user.cart_page       import CartPage
        from frontend.pages.user.profile_page    import ProfilePage
        from frontend.pages.user.campaigns_page  import CampaignsPage
        from frontend.pages.user.categories_page import CategoriesPage
        from frontend.pages.user.orders_page     import OrdersPage
        from frontend.pages.user.checkout_page   import CheckoutPage

        self._pages = [
            HomePage(self._ctx),       # 0
            CatalogPage(self._ctx),    # 1
            FavoritesPage(self._ctx),  # 2
            CartPage(self._ctx),       # 3  PAGE_CART
            ProfilePage(self._ctx),    # 4
            CampaignsPage(self._ctx),  # 5  PAGE_CAMPAIGNS
            CategoriesPage(self._ctx), # 6  PAGE_CATEGORIES
            OrdersPage(self._ctx),     # 7  PAGE_ORDERS
            CheckoutPage(self._ctx),   # 8  PAGE_CHECKOUT
        ]
        for p in self._pages:
            self._stack.addWidget(p)

        # Kampanya kartına tıklama → katalog sayfasını kategoriyle filtrele
        campaigns_page: CampaignsPage = self._pages[self.PAGE_CAMPAIGNS]
        campaigns_page.category_selected.connect(
            lambda cat: self._on_catalog_filter(cat, "")
        )

        # Kategori / alt-kategori seçimi → katalog sayfasına yönlendir
        categories_page: CategoriesPage = self._pages[self.PAGE_CATEGORIES]
        categories_page.category_selected.connect(self._on_catalog_filter)

        # Sepet → "Ödemeye Geç" → CheckoutPage
        cart_page: CartPage = self._pages[self.PAGE_CART]
        cart_page.checkout_requested.connect(self._open_checkout)
        cart_page.cart_changed.connect(self.refresh_cart_bar)

        # Checkout → sipariş tamamlandı → OrderSuccessDialog
        checkout_page: CheckoutPage = self._pages[self.PAGE_CHECKOUT]
        checkout_page.order_completed.connect(self._on_order_completed)
        checkout_page.back_to_cart.connect(
            lambda: self._go_label("Sepetim", self.PAGE_CART)
        )

    # ── Navigasyon ────────────────────────────────────────────

    def _go_label(self, label: str, page_idx: int) -> None:
        for i, (_, lbl, _) in enumerate(self._NAV_ITEMS):
            self._nav_buttons[i].setStyleSheet(self._nav_style(lbl == label))
        self._go_idx(page_idx)

    def _go_idx(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        page = self._pages[idx]
        if hasattr(page, "refresh"):
            page.refresh()
        # Sayfa değişince cart bar'ı her ihtimale karşı tazele
        self.refresh_cart_bar()

    # ── Sepet Barı ────────────────────────────────────────────

    def refresh_cart_bar(self) -> None:
        """
        Sepet içeriği değiştiğinde alt CartBar'ı günceller.
        Tüm sepete-ekle/çıkar/değiştir noktaları bu metodu çağırmalıdır.
        """
        user = self._ctx.auth_service.get_current_user()
        if not user:
            self._cart_bar.update_state(0, 0.0)
            return

        items = self._ctx.cart_service.get_cart_items(user.id)
        if not items:
            self._cart_bar.update_state(0, 0.0)
            return

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        total = 0.0
        count = 0
        for it in items:
            unit = self._ctx.price_calculator.calculate(it["product"], gold)
            total += unit * it["quantity"]
            count += it["quantity"]
        self._cart_bar.update_state(count, total)

    # ── Checkout akışı ────────────────────────────────────────

    def _open_checkout(self) -> None:
        checkout = self._pages[self.PAGE_CHECKOUT]
        checkout.start()
        # Eğer sepet boşsa start() içinden back_to_cart emit edilir → orada zaten
        # cart sayfasına dönülür. Doluysa checkout'a geçeriz.
        user = self._ctx.auth_service.get_current_user()
        if user and self._ctx.cart_service.cart_count(user.id) > 0:
            # Stack içinde checkout sayfasına git ama nav'da yine "Sepetim" aktif kalsın.
            self._stack.setCurrentIndex(self.PAGE_CHECKOUT)

    def _on_order_completed(self, order) -> None:
        """Sipariş başarıyla oluşturuldu — başarı modalı, sepeti temizle, listele."""
        self.refresh_cart_bar()  # sepet artık boş
        dlg = OrderSuccessDialog(order, parent=self)
        dlg.view_orders_clicked.connect(
            lambda: self._go_label("Siparişlerim", self.PAGE_ORDERS)
        )
        dlg.exec()
        # Modal kapatıldıktan sonra (Siparişlerim seçilmediyse) sepete geri dön
        if self._stack.currentIndex() == self.PAGE_CHECKOUT:
            self._go_label("Sepetim", self.PAGE_CART)

    def _on_search(self) -> None:
        query = self._search.text().strip()
        if query:
            catalog = self._pages[1]
            if hasattr(catalog, "search"):
                catalog.search(query)
            self._go_idx(1)

    def _on_catalog_filter(self, category: str, subcategory: str = "") -> None:
        """Kampanya/Kategoriler sayfasından gelen filtreyi katalog'a uygula."""
        catalog = self._pages[1]
        if hasattr(catalog, "filter_by_category"):
            catalog.filter_by_category(category, subcategory)
        self._go_label("Ürünler", 1)

    # ── Otomatik kur yenileme (60 sn, worker thread) ─────────

    def _start_rate_timer(self) -> None:
        self._fetch_rates()
        self._rate_timer = QTimer(self)
        self._rate_timer.timeout.connect(self._fetch_rates)
        self._rate_timer.start(60_000)

    def _fetch_rates(self) -> None:
        if self._rate_worker and self._rate_worker.isRunning():
            return
        self._rate_worker = _RateWorker(
            self._ctx.exchange_service,
            self._ctx.rate_api,
        )
        self._rate_worker.fetched.connect(self._on_rates_done)
        self._rate_worker.start()

    def _on_rates_done(self, result: dict) -> None:
        rates   = result.get("rates")
        btc_usd = result.get("btc_usd")
        # Ana sayfanın canlı kur kartlarını güncelle
        home = self._pages[0]
        if hasattr(home, "set_live_rates"):
            home.set_live_rates(rates, btc_usd)

    # ── Çıkış ─────────────────────────────────────────────────

    def _logout(self) -> None:
        if hasattr(self, "_rate_timer"):
            self._rate_timer.stop()
        self._ctx.auth_service.logout()
        from frontend.windows.login_window import LoginWindow
        win = LoginWindow(self._ctx)
        win.show()
        self.close()
