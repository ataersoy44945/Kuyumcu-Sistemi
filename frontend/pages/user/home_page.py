"""
Ana Sayfa — Kullanıcı panelinin premium landing ekranı.
Canlı kur kartları · Hero banner · Kategori chip'leri ·
Ürün ızgarası · Sağ bilgi paneli · Servis avantajları
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Fonts, Radius
from frontend.components.product_card import ProductCard
from frontend.components.toast import Toast
from frontend.dialogs.product_detail_dialog import ProductDetailDialog


# ════════════════════════════════════════════════════════════
#  CANLÜ KUR KARTI
# ════════════════════════════════════════════════════════════

class _LiveRateCard(QFrame):
    """Tek bir döviz/altın kurunu gösteren canlı veri kartı."""

    def __init__(self, icon: str, ticker: str, color: str):
        super().__init__()
        self._color      = color
        self._prev_value: float | None = None

        self.setMinimumWidth(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(82)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-top: 2px solid {color};
                border-radius: {Radius.MD};
            }}
            QFrame:hover {{
                background: {Colors.BG_ELEVATED};
                border-top-color: {color};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(3)

        # Üst satır: ticker + trend ikonu
        top = QHBoxLayout()
        top.setSpacing(4)
        ticker_lbl = QLabel(f"{icon}  {ticker}")
        ticker_lbl.setStyleSheet(
            f"color: {color}; font-size: 9px; font-weight: 700; "
            f"background: transparent; border: none; letter-spacing: 0.3px;"
        )
        self._trend = QLabel("")
        self._trend.setStyleSheet(
            "font-size: 11px; font-weight: 700; background: transparent; border: none;"
        )
        top.addWidget(ticker_lbl)
        top.addStretch()
        top.addWidget(self._trend)
        lay.addLayout(top)

        # Değer
        self._val = QLabel("—")
        self._val.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none; font-family: {Fonts.FAMILY_M};"
        )
        lay.addWidget(self._val)

    def update(self, display: str, raw: float) -> None:
        """Değeri günceller; önceki değerle karşılaştırarak trend gösterir."""
        if self._prev_value is not None:
            if raw > self._prev_value:
                self._trend.setText("▲")
                self._trend.setStyleSheet(
                    f"color: {Colors.GREEN}; font-size: 12px; font-weight: 700; "
                    f"background: transparent; border: none;"
                )
            elif raw < self._prev_value:
                self._trend.setText("▼")
                self._trend.setStyleSheet(
                    f"color: {Colors.RED}; font-size: 12px; font-weight: 700; "
                    f"background: transparent; border: none;"
                )
        self._prev_value = raw
        self._val.setText(display)


# ════════════════════════════════════════════════════════════
#  HERO BANNER
# ════════════════════════════════════════════════════════════

class _HeroBanner(QFrame):
    explore_clicked = None   # dışarıdan atanır

    def __init__(self):
        super().__init__()
        self.setFixedHeight(150)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0A1628,
                    stop:0.5 #0F1E38,
                    stop:1 rgba(212,175,55,0.12));
                border: 1px solid rgba(212,175,55,0.25);
                border-radius: {Radius.LG};
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(32, 0, 32, 0)
        lay.setSpacing(0)

        # Sol: metin
        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        eyebrow = QLabel("✦  YENİ KOLEKSİYON")
        eyebrow.setStyleSheet(
            f"color: {Colors.GOLD_DIM}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 2px; background: transparent; border: none;"
        )

        headline = QLabel("Zarafetin Altın Çağı")
        headline.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none;"
        )

        subtext = QLabel("El işçiliğiyle şekillendirilmiş, kalıcı değer taşıyan mücevherler.")
        subtext.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 11px; "
            f"background: transparent; border: none;"
        )

        btn_explore = QPushButton("  Koleksiyonu Keşfet  →")
        btn_explore.setFixedSize(180, 34)
        btn_explore.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_explore.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});
                color: {Colors.TEXT_ON_GOLD};
                border: none; border-radius: {Radius.FULL};
                font-size: 11px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #FFD700, stop:1 {Colors.GOLD_BRIGHT});
            }}
        """)
        if self.explore_clicked:
            btn_explore.clicked.connect(self.explore_clicked)

        text_col.addWidget(eyebrow)
        text_col.addWidget(headline)
        text_col.addWidget(subtext)
        text_col.addSpacing(4)
        text_col.addWidget(btn_explore, alignment=Qt.AlignmentFlag.AlignLeft)

        # Sağ: dekoratif alan
        deco = QLabel("💎")
        deco.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deco.setStyleSheet(
            "font-size: 72px; background: transparent; border: none;"
        )

        lay.addLayout(text_col, 2)
        lay.addWidget(deco, 1)


# ════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ════════════════════════════════════════════════════════════

def _section_title(text: str, sub: str = "") -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(3)
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {Colors.TEXT_H1}; font-size: 16px; font-weight: 700; border: none;"
    )
    lay.addWidget(lbl)
    if sub:
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; border: none;"
        )
        lay.addWidget(sub_lbl)
    return w


def _info_card(icon: str, title: str, body: str, accent: str = None) -> QFrame:
    accent = accent or Colors.GOLD
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {Colors.BG_SURFACE};
            border: 1px solid {Colors.BORDER_DIM};
            border-top: 3px solid {accent};
            border-radius: {Radius.LG};
        }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(6)

    hdr = QHBoxLayout()
    ico = QLabel(icon)
    ico.setStyleSheet("font-size: 20px; border: none; background: transparent;")
    ttl = QLabel(title)
    ttl.setStyleSheet(
        f"color: {accent}; font-size: 13px; font-weight: 700; border: none;"
    )
    hdr.addWidget(ico)
    hdr.addSpacing(6)
    hdr.addWidget(ttl)
    hdr.addStretch()
    lay.addLayout(hdr)

    body_lbl = QLabel(body)
    body_lbl.setStyleSheet(
        f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
    )
    body_lbl.setWordWrap(True)
    lay.addWidget(body_lbl)
    return f


# ════════════════════════════════════════════════════════════
#  ANA SAYFA
# ════════════════════════════════════════════════════════════

class HomePage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    # ── UI inşa ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setGeometry(0, 0, 9999, 9999)

        inner = QWidget()
        inner.setStyleSheet(f"background: {Colors.BG_BASE};")
        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        lay = QVBoxLayout(inner)
        lay.setContentsMargins(24, 16, 24, 24)
        lay.setSpacing(16)

        # 1 ── Canlı kur kartları satırı ─────────────────────
        lay.addWidget(self._build_rate_section())

        # 2 ── İçerik + sağ panel ─────────────────────────────
        mid = QHBoxLayout()
        mid.setSpacing(14)
        mid.addWidget(self._build_main_column(), 1)
        mid.addWidget(self._build_right_panel())
        lay.addLayout(mid)

        # 3 ── Servis avantajları ─────────────────────────────
        lay.addWidget(self._build_service_row())
        lay.addStretch()

    # ── 1: Canlı kur satırı ───────────────────────────────────

    def _build_rate_section(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        # Başlık satırı: "Canlı Veri" + güncelleme zamanı
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {Colors.GREEN}; font-size: 10px; border: none;")
        live_lbl = QLabel("CANLI VERİ")
        live_lbl.setStyleSheet(
            f"color: {Colors.GREEN}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1px; border: none;"
        )
        self._update_lbl = QLabel("Yükleniyor…")
        self._update_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; border: none;"
        )
        header.addWidget(dot)
        header.addSpacing(4)
        header.addWidget(live_lbl)
        header.addSpacing(12)
        header.addWidget(self._update_lbl)
        header.addStretch()
        lay.addLayout(header)

        # Kur kartları
        cards_row = QHBoxLayout()
        cards_row.setSpacing(8)
        self._rc_usd     = _LiveRateCard("💵", "USD / TRY",     Colors.BLUE)
        self._rc_eur     = _LiveRateCard("💶", "EUR / TRY",     Colors.GREEN)
        self._rc_gram    = _LiveRateCard("🪙", "GRAM ALTIN",    Colors.GOLD)
        self._rc_quarter = _LiveRateCard("🪙", "ÇEYREK ALTIN",  Colors.GOLD)
        self._rc_btc     = _LiveRateCard("₿",  "BTC / TRY",    Colors.BTC)

        for rc in (self._rc_usd, self._rc_eur, self._rc_gram, self._rc_quarter, self._rc_btc):
            cards_row.addWidget(rc)
        lay.addLayout(cards_row)
        return container

    # ── 2a: Sol/orta içerik sütunu ────────────────────────────

    def _build_main_column(self) -> QWidget:
        w = QWidget()
        # Sütunu dış taşmalara karşı hizala — ana row'un stretch'ine uyar
        w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        # Hero banner
        lay.addWidget(_HeroBanner())

        # Kategori chip'leri — yatay kaydırılabilir
        lay.addWidget(_section_title("✦  Kategoriler", "Koleksiyona göz atın"))
        self._cat_scroll = QScrollArea()
        self._cat_scroll.setFixedHeight(44)
        self._cat_scroll.setWidgetResizable(True)
        self._cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cat_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        cat_inner = QWidget()
        cat_inner.setStyleSheet("background: transparent;")
        self._cat_row = QHBoxLayout(cat_inner)
        self._cat_row.setContentsMargins(0, 2, 0, 2)
        self._cat_row.setSpacing(8)
        self._cat_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._cat_scroll.setWidget(cat_inner)
        lay.addWidget(self._cat_scroll)

        # Ürünler
        lay.addWidget(
            _section_title("⭐  Öne Çıkan Ürünler", "En çok tercih edilen tasarımlar")
        )
        self._product_grid = QGridLayout()
        self._product_grid.setSpacing(12)
        self._product_grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lay.addLayout(self._product_grid)
        return w

    # ── 2b: Sağ bilgi paneli ──────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(240)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Kampanya kartı
        kampanya = _info_card(
            "🎁", "Özel Fırsatlar",
            "Bu hafta bilezik koleksiyonunda\n%15 indirim fırsatını kaçırmayın!",
            Colors.AMBER,
        )
        lay.addWidget(kampanya)

        # Güvenli alışveriş
        guvenli = _info_card(
            "🔒", "Güvenli Alışveriş",
            "SSL şifreli ödeme · Sertifikalı altın güvencesi · 14 gün iade hakkı",
            Colors.GREEN,
        )
        lay.addWidget(guvenli)

        # Son incelenenler
        recent = QFrame()
        recent.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-radius: {Radius.LG};
            }}
        """)
        r_lay = QVBoxLayout(recent)
        r_lay.setContentsMargins(16, 14, 16, 14)
        r_lay.setSpacing(8)
        r_lbl = QLabel("🕐  Son İncelenenler")
        r_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700; border: none;"
        )
        r_lay.addWidget(r_lbl)
        self._recent_lay = QVBoxLayout()
        self._recent_lay.setSpacing(6)
        r_lay.addLayout(self._recent_lay)
        lay.addWidget(recent)

        lay.addStretch()
        return w

    # ── 3: Servis avantajları ─────────────────────────────────

    def _build_service_row(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setSpacing(14)

        services = [
            ("🚚", "Ücretsiz Kargo",  "500 TL üzeri siparişlerde"),
            ("🔒", "Güvenli Ödeme",   "256-bit SSL şifreleme"),
            ("🔄", "Kolay İade",      "14 gün içinde iade garantisi"),
            ("💬", "Canlı Destek",    "7/24 müşteri hizmetleri"),
        ]
        for icon, title, desc in services:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG_SURFACE};
                    border: 1px solid {Colors.BORDER_DIM};
                    border-radius: {Radius.LG};
                }}
                QFrame:hover {{
                    background: {Colors.BG_ELEVATED};
                    border-color: {Colors.GOLD_SUBTLE};
                }}
            """)
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(16, 14, 16, 14)
            c_lay.setSpacing(12)

            ico = QLabel(icon)
            ico.setStyleSheet(
                f"font-size: 24px; color: {Colors.GOLD}; border: none; background: transparent;"
            )
            ico.setFixedWidth(32)

            txt = QVBoxLayout()
            txt.setSpacing(2)
            ttl = QLabel(title)
            ttl.setStyleSheet(
                f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600; border: none;"
            )
            dsc = QLabel(desc)
            dsc.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
            )
            txt.addWidget(ttl)
            txt.addWidget(dsc)

            c_lay.addWidget(ico)
            c_lay.addLayout(txt)
            lay.addWidget(card, 1)
        return w

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        self._load_categories()
        self._load_products()
        self._load_recent_placeholder()

    def set_live_rates(self, rates, btc_usd: float = None) -> None:
        """UserWindow worker thread'inden çağrılır — kur kartlarını günceller."""
        if not rates:
            return

        self._rc_usd.update(f"₺ {rates.usd_try:,.4f}", rates.usd_try)
        self._rc_eur.update(f"₺ {rates.eur_try:,.4f}", rates.eur_try)
        self._rc_gram.update(f"₺ {rates.gold_gram_try:,.2f}", rates.gold_gram_try)

        if rates.gold_quarter_try:
            self._rc_quarter.update(f"₺ {rates.gold_quarter_try:,.2f}", rates.gold_quarter_try)

        if btc_usd and rates.usd_try:
            btc_try = btc_usd * rates.usd_try
            self._rc_btc.update(f"₺ {btc_try:,.0f}", btc_try)
        elif btc_usd:
            self._rc_btc.update(f"${btc_usd:,.0f}", btc_usd)

        ts = self._ctx.exchange_service.last_update_label()
        self._update_lbl.setText(ts.replace("Son güncelleme: ", "↻  "))

    # ── Kategori chip'leri ────────────────────────────────────

    def _load_categories(self) -> None:
        while self._cat_row.count():
            item = self._cat_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # "Tümü" butonu
        all_btn = self._chip_btn("Tümü", active=True)
        self._cat_row.addWidget(all_btn)

        cats = self._ctx.product_service.get_categories()
        for c in cats:
            btn = self._chip_btn(c.name)
            self._cat_row.addWidget(btn)

    def _chip_btn(self, text: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if active:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.GOLD_SUBTLE};
                    color: {Colors.GOLD};
                    border: 1px solid {Colors.GOLD}80;
                    border-radius: {Radius.FULL};
                    font-size: 11px; font-weight: 600;
                    padding: 0 14px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_BODY};
                    border: 1px solid {Colors.BORDER_DEFAULT};
                    border-radius: {Radius.FULL};
                    font-size: 11px; padding: 0 14px;
                }}
                QPushButton:hover {{
                    background: {Colors.GOLD_SUBTLE};
                    color: {Colors.GOLD};
                    border-color: {Colors.GOLD}80;
                }}
            """)
        return btn

    # ── Ürün ızgarası ─────────────────────────────────────────

    def _load_products(self) -> None:
        # Mevcut widget'ları temizle
        while self._product_grid.count():
            item = self._product_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        user  = self._ctx.auth_service.get_current_user()

        products = self._ctx.product_service.get_most_favorited(6)
        for i, p in enumerate(products):
            price  = self._ctx.price_calculator.calculate(p, gold)
            is_fav = self._ctx.favorite_service.is_favorite(user.id, p.id)
            card   = ProductCard(p, price, is_fav)
            card.favorite_toggled.connect(self._toggle_fav)
            card.cart_requested.connect(self._add_to_cart)
            card.detail_requested.connect(self._open_detail)
            self._product_grid.addWidget(card, i // 3, i % 3)

    # ── Ürün aksiyonları ──────────────────────────────────────

    def _toggle_fav(self, product_id: int, _: bool) -> None:
        user = self._ctx.auth_service.get_current_user()
        self._ctx.favorite_service.toggle(user.id, product_id)

    def _add_to_cart(self, product_id: int) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return
        qty = self._ctx.cart_service.add_to_cart(user.id, product_id, 1)
        Toast.show_success(self, f"Sepete eklendi  (toplam {qty} adet)")

    def _open_detail(self, product_id: int) -> None:
        product = self._ctx.product_service.get_by_id(product_id)
        if not product:
            return
        dlg = ProductDetailDialog(self._ctx, product, parent=self)
        dlg.exec()

    # ── Son incelenenler (placeholder) ───────────────────────

    def _load_recent_placeholder(self) -> None:
        while self._recent_lay.count():
            item = self._recent_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        products = self._ctx.product_service.get_most_favorited(3)
        rates    = self._ctx.exchange_service.get_rates()
        gold     = rates.gold_gram_try if rates else 0.0

        for p in products:
            price = self._ctx.price_calculator.calculate(p, gold)
            row   = QHBoxLayout()
            name  = QLabel(p.name[:22] + ("…" if len(p.name) > 22 else ""))
            name.setStyleSheet(
                f"color: {Colors.TEXT_BODY}; font-size: 12px; border: none;"
            )
            prc = QLabel(f"₺{price:,.0f}")
            prc.setStyleSheet(
                f"color: {Colors.GOLD}; font-size: 12px; font-weight: 600; border: none;"
            )
            row.addWidget(name)
            row.addStretch()
            row.addWidget(prc)

            item_w = QWidget()
            item_w.setLayout(row)
            self._recent_lay.addWidget(item_w)

        if not products:
            empty = QLabel("Henüz incelenen ürün yok.")
            empty.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
            )
            self._recent_lay.addWidget(empty)
