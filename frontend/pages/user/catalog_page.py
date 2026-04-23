from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QLineEdit, QComboBox, QGridLayout,
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from config import KARAT_COEFFICIENTS
from frontend.styles.app_theme import Colors, input_field
from frontend.components.product_card import ProductCard
from frontend.components.toast import Toast
from frontend.dialogs.product_detail_dialog import ProductDetailDialog
from frontend.utils import product_subcategory


# ProductCard genişliği sabit (210px) + spacing (16px)
_CARD_W     = 210
_CARD_GAP   = 16
_SIDE_PAD   = 24    # grid solu/sağı
_MIN_COLS   = 1
_MAX_COLS   = 6


class CatalogPage(QWidget):
    """Ürün kataloğu — ekran genişliğine göre sütun sayısı otomatik ayarlanır."""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._cards: list[ProductCard] = []
        self._current_cols = 4
        self._sub_filter: str = ""   # ek alt-kategori filtresi (örn. "Taşlı")
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_filter_bar())
        root.addWidget(self._build_grid_area(), 1)
        self._build_empty_state(root)

    def _build_filter_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(60)
        bar.setStyleSheet(
            f"background: {Colors.BG_SURFACE}; "
            f"border-bottom: 1px solid {Colors.BORDER_DEFAULT};"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(_SIDE_PAD, 0, _SIDE_PAD, 0)
        lay.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Ürün ara…")
        self._search.setFixedSize(260, 38)
        self._search.setStyleSheet(input_field())
        self._search.textChanged.connect(self._on_user_filter_change)

        self._cat_cb = QComboBox()
        self._cat_cb.setFixedSize(180, 38)
        self._cat_cb.setStyleSheet(input_field())
        self._cat_cb.currentIndexChanged.connect(self._on_user_filter_change)

        self._karat_cb = QComboBox()
        self._karat_cb.setFixedSize(140, 38)
        self._karat_cb.setStyleSheet(input_field())
        self._karat_cb.addItem("Tüm Ayarlar", None)
        for k in KARAT_COEFFICIENTS:
            self._karat_cb.addItem(f"{k} Ayar", k)
        self._karat_cb.currentIndexChanged.connect(self._on_user_filter_change)

        self._count_lbl = QLabel("Ürünler yükleniyor…")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px;"
        )

        lay.addWidget(self._search)
        lay.addWidget(self._cat_cb)
        lay.addWidget(self._karat_cb)
        lay.addStretch()
        lay.addWidget(self._count_lbl)
        return bar

    def _build_grid_area(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Dış container — grid'i yatayda ortalar (sol-sağ stretch)
        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet(f"background: {Colors.BG_BASE};")
        outer = QVBoxLayout(self._grid_widget)
        outer.setContentsMargins(_SIDE_PAD, 20, _SIDE_PAD, 20)
        outer.setSpacing(0)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(_CARD_GAP)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        row.addStretch()
        row.addLayout(self._grid)
        row.addStretch()

        outer.addLayout(row)
        outer.addStretch()

        scroll.setWidget(self._grid_widget)
        return scroll

    def _build_empty_state(self, root: QVBoxLayout) -> None:
        self._empty_lbl = QLabel(
            "🔍\nArama kriterlerine uygun ürün bulunamadı.\nFarklı bir filtre deneyin."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 80px; "
            f"background: transparent;"
        )
        self._empty_lbl.hide()
        root.addWidget(self._empty_lbl)

    # ── Responsive sütun sayısı ───────────────────────────────

    def _compute_cols(self) -> int:
        w = self.width() - (_SIDE_PAD * 2)
        if w <= _CARD_W:
            return _MIN_COLS
        cols = (w + _CARD_GAP) // (_CARD_W + _CARD_GAP)
        return max(_MIN_COLS, min(_MAX_COLS, int(cols)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        new_cols = self._compute_cols()
        if new_cols != self._current_cols and self._cards:
            self._current_cols = new_cols
            self._relayout_cards()

    def _relayout_cards(self) -> None:
        """Mevcut kartları grid'den çıkarır, yeni sütun sayısıyla yerleştirir."""
        while self._grid.count():
            self._grid.takeAt(0)
        for i, card in enumerate(self._cards):
            self._grid.addWidget(card, i // self._current_cols, i % self._current_cols)

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        self._cat_cb.blockSignals(True)
        self._cat_cb.clear()
        self._cat_cb.addItem("Tüm Kategoriler", None)
        for c in self._ctx.product_service.get_categories():
            self._cat_cb.addItem(c.name, c.id)
        self._cat_cb.blockSignals(False)
        self._apply_filters()

    def search(self, query: str) -> None:
        self._search.setText(query)

    def filter_by_category(self, category_name: str,
                            subcategory: str = "") -> None:
        """
        Kampanya veya Kategoriler sayfasından gelen filtreyi uygular.
        - category_name: DB'deki kategori adı (boş → tümü)
        - subcategory:   "Alt: X" değeri (boş → alt filtre yok)

        Tüm widget sinyalleri bloklanır — alt_filter bozulmadan uygulanır.
        """
        # İçeride tutulan alt-kategori değeri
        self._sub_filter = subcategory or ""

        # Sinyalleri geçici olarak kapat ki user handler çağrılmasın
        for w in (self._search, self._cat_cb, self._karat_cb):
            w.blockSignals(True)

        self._search.clear()
        self._karat_cb.setCurrentIndex(0)

        target_idx = 0
        if category_name:
            for i in range(self._cat_cb.count()):
                if self._cat_cb.itemText(i).lower() == category_name.lower():
                    target_idx = i
                    break
        self._cat_cb.setCurrentIndex(target_idx)

        for w in (self._search, self._cat_cb, self._karat_cb):
            w.blockSignals(False)

        # Tek seferde uygula
        self._apply_filters()

    def _on_user_filter_change(self) -> None:
        """Kullanıcı kendi manuel filtre değiştirdi → alt kategoriyi temizle."""
        self._sub_filter = ""
        self._apply_filters()

    def _apply_filters(self) -> None:
        query  = self._search.text().strip()
        cat_id = self._cat_cb.currentData()
        karat  = self._karat_cb.currentData()

        products = self._ctx.product_service.search(
            query=query, karat=karat, category_id=cat_id, for_sale_only=True
        )
        # Alt-kategori filtresi (Kategoriler sayfasından geliyor)
        if self._sub_filter:
            sub = self._sub_filter.lower()
            products = [
                p for p in products
                if (product_subcategory(p) or "").lower() == sub
            ]
        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        user  = self._ctx.auth_service.get_current_user()

        # Önceki kartları temizle
        for card in self._cards:
            card.setParent(None)
        self._cards.clear()

        if not products:
            self._empty_lbl.show()
            self._count_lbl.setText("0 ürün")
            return

        self._empty_lbl.hide()
        self._count_lbl.setText(f"{len(products)} ürün")

        self._current_cols = self._compute_cols()
        for i, p in enumerate(products):
            price  = self._ctx.price_calculator.calculate(p, gold)
            is_fav = self._ctx.favorite_service.is_favorite(user.id, p.id) if user else False
            card   = ProductCard(p, price, is_fav)
            card.favorite_toggled.connect(self._toggle_fav)
            card.cart_requested.connect(self._add_to_cart)
            card.detail_requested.connect(self._open_detail)
            self._grid.addWidget(card, i // self._current_cols, i % self._current_cols)
            self._cards.append(card)

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
        # Favori değişirse kart durumunu tazele
        dlg.favorite_changed.connect(lambda pid, _fav: self._apply_filters())
        dlg.exec()
