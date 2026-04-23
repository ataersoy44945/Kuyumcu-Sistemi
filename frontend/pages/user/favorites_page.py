from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors
from frontend.components.product_card import ProductCard
from frontend.components.toast import Toast
from frontend.dialogs.product_detail_dialog import ProductDetailDialog


_CARD_W   = 210
_CARD_GAP = 16
_SIDE_PAD = 28
_MIN_COLS = 1
_MAX_COLS = 6


class FavoritesPage(QWidget):
    """Favoriler — ekran genişliğine göre sütun sayısı otomatik ayarlanır."""

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._cards: list[ProductCard] = []
        self._current_cols = 4
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(_SIDE_PAD, 20, _SIDE_PAD, 20)
        root.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("❤️  Favorilerim")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 20px; font-weight: 700;"
        )
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 13px;"
        )
        header.addWidget(title)
        header.addSpacing(12)
        header.addWidget(self._count_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        root.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Grid'i dış container ile yatayda ortala
        self._grid_w = QWidget()
        self._grid_w.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(self._grid_w)
        outer.setContentsMargins(0, 0, 0, 0)
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

        scroll.setWidget(self._grid_w)
        root.addWidget(scroll, 1)

        self._empty_lbl = QLabel(
            "💔\nHenüz favoriniz yok.\nÜrünlerin üzerindeki ♡ butonuna tıklayarak ekleyebilirsiniz."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 80px;"
        )
        self._empty_lbl.hide()
        root.addWidget(self._empty_lbl)

    # ── Responsive grid ───────────────────────────────────────

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
        while self._grid.count():
            self._grid.takeAt(0)
        for i, card in enumerate(self._cards):
            self._grid.addWidget(card, i // self._current_cols, i % self._current_cols)

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        user     = self._ctx.auth_service.get_current_user()
        products = self._ctx.favorite_service.get_user_favorites(user.id)

        for card in self._cards:
            card.setParent(None)
        self._cards.clear()

        if not products:
            self._empty_lbl.show()
            self._count_lbl.setText("")
            return

        self._empty_lbl.hide()
        self._count_lbl.setText(f"({len(products)} ürün)")

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0

        self._current_cols = self._compute_cols()
        for i, p in enumerate(products):
            price = self._ctx.price_calculator.calculate(p, gold)
            card  = ProductCard(p, price, is_favorite=True)
            card.favorite_toggled.connect(lambda pid, _: self._remove_fav(pid))
            card.cart_requested.connect(self._add_to_cart)
            card.detail_requested.connect(self._open_detail)
            self._grid.addWidget(card, i // self._current_cols, i % self._current_cols)
            self._cards.append(card)

    # ── Ürün aksiyonları ──────────────────────────────────────

    def _remove_fav(self, product_id: int) -> None:
        user = self._ctx.auth_service.get_current_user()
        self._ctx.favorite_service.toggle(user.id, product_id)
        self.refresh()

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
        dlg.favorite_changed.connect(lambda pid, fav: self.refresh() if not fav else None)
        dlg.exec()
