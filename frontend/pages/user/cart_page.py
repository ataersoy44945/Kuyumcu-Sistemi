"""
Sepet Sayfası — CartService üzerinden çalışır.
  - adet artır/azalt
  - ürün sil
  - toplam otomatik hesaplanır
  - "Sipariş Ver" butonu sepeti siparişe çevirir
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.app_context import AppContext
from backend.services.order_service import (
    SHIPPING_FREE_THRESHOLD, calculate_shipping,
)
from frontend.styles.app_theme import Colors, Fonts, Radius, gold_btn
from frontend.components.toast import Toast


class _CartRow(QFrame):
    """Sepetteki tek bir satır — ürün + adet + fiyat + sil."""

    def __init__(self, item: dict, unit_price: float, on_qty_change, on_remove):
        super().__init__()
        self._product    = item["product"]
        self._quantity   = item["quantity"]
        self._unit_price = unit_price
        self._on_qty     = on_qty_change
        self._on_remove  = on_remove

        self.setFixedHeight(88)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-radius: {Radius.MD};
            }}
            QFrame:hover {{ background: {Colors.BG_ELEVATED}; }}
        """)
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(16)

        # Mini kategori ikonu
        from frontend.utils import category_icon
        ico_lbl = QLabel(category_icon(self._product.category_name or ""))
        ico_lbl.setFixedSize(56, 56)
        ico_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico_lbl.setStyleSheet(f"""
            background: {Colors.BG_ELEVATED};
            border: 1px solid {Colors.BORDER_DIM};
            border-radius: {Radius.SM};
            font-size: 28px;
        """)
        lay.addWidget(ico_lbl)

        # İsim + özellikler
        col = QVBoxLayout()
        col.setSpacing(3)
        name = QLabel(self._product.name)
        name.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700; border: none;"
        )
        meta = QLabel(
            f"{self._product.category_name or '—'}  ·  "
            f"{self._product.karat} Ayar  ·  "
            f"{self._product.weight_grams:.2f} gr"
        )
        meta.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        col.addWidget(name)
        col.addWidget(meta)
        lay.addLayout(col, 1)

        # Adet kontrolü
        qty_box = QHBoxLayout()
        qty_box.setSpacing(4)

        btn_minus = self._qty_button("−")
        btn_minus.clicked.connect(lambda: self._change_qty(-1))

        self._qty_lbl = QLabel(str(self._quantity))
        self._qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qty_lbl.setFixedSize(40, 28)
        self._qty_lbl.setStyleSheet(f"""
            color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700;
            background: {Colors.BG_INPUT};
            border: 1px solid {Colors.BORDER_DEFAULT};
            border-radius: {Radius.SM};
        """)

        btn_plus = self._qty_button("+")
        btn_plus.clicked.connect(lambda: self._change_qty(+1))

        qty_box.addWidget(btn_minus)
        qty_box.addWidget(self._qty_lbl)
        qty_box.addWidget(btn_plus)

        qty_w = QWidget()
        qty_w.setLayout(qty_box)
        lay.addWidget(qty_w)

        # Toplam fiyat
        self._price_lbl = QLabel(self._total_text())
        self._price_lbl.setFixedWidth(130)
        self._price_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._price_lbl.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 15px; font-weight: 700; "
            f"font-family: {Fonts.FAMILY}; border: none;"
        )
        lay.addWidget(self._price_lbl)

        # Sil butonu
        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(32, 32)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setToolTip("Ürünü sil")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.RED};
                border: 1px solid {Colors.RED}44; border-radius: 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {Colors.RED_BG}; border-color: {Colors.RED};
            }}
        """)
        btn_del.clicked.connect(self._remove)
        lay.addWidget(btn_del)

    def _qty_button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.GOLD};
                border: 1px solid {Colors.GOLD}66; border-radius: {Radius.SM};
                font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: {Colors.GOLD_SUBTLE}; border-color: {Colors.GOLD};
            }}
        """)
        return btn

    def _total_text(self) -> str:
        return f"₺ {self._unit_price * self._quantity:,.2f}"

    def _change_qty(self, delta: int) -> None:
        new_qty = self._quantity + delta
        if new_qty <= 0:
            self._remove()
            return
        # Stok kontrolü
        if new_qty > self._product.stock_quantity:
            Toast.show_error(self, f"Stokta {self._product.stock_quantity} adet kaldı")
            return
        self._quantity = new_qty
        self._qty_lbl.setText(str(new_qty))
        self._price_lbl.setText(self._total_text())
        self._on_qty(self._product.id, new_qty)

    def _remove(self) -> None:
        self._on_remove(self._product.id, self._product.name)


class CartPage(QWidget):
    """Kullanıcının sepet sayfası."""

    checkout_requested = pyqtSignal()   # "Ödemeye Geç" basıldığında
    cart_changed       = pyqtSignal()   # Sepet güncellenince (CartBar'ı yenilemek için)

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx   = ctx
        self._rows: list[_CartRow] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # Başlık
        header = QHBoxLayout()
        title = QLabel("🛒  Sepetim")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 20px; font-weight: 700;"
        )
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 12px; font-weight: 700; "
            f"border: 1px solid {Colors.GOLD}55; border-radius: {Radius.FULL}; "
            f"padding: 5px 12px; background: {Colors.GOLD_SUBTLE};"
        )
        header.addWidget(title)
        header.addSpacing(12)
        header.addWidget(self._count_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        header.addStretch()
        root.addLayout(header)

        # Satır listesi (scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(10)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._list_w)
        root.addWidget(scroll, 1)

        # Boş durum
        self._empty_lbl = QLabel(
            "🛒\nSepetiniz boş.\nÜrünler sayfasından alışverişe başlayabilirsiniz."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 80px;"
        )
        self._empty_lbl.hide()
        root.addWidget(self._empty_lbl)

        # Alt: Sipariş Özeti (ara toplam + kargo + genel toplam + Ödemeye Geç)
        bottom = QFrame()
        bottom.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_RAISED};
                border: 1px solid {Colors.GOLD}33;
                border-radius: {Radius.LG};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        b_lay = QVBoxLayout(bottom)
        b_lay.setContentsMargins(22, 16, 22, 16)
        b_lay.setSpacing(8)

        head = QLabel("📋  Sipariş Özeti")
        head.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 13px; font-weight: 700; letter-spacing: 0.4px;"
        )
        b_lay.addWidget(head)
        b_lay.addSpacing(2)

        # Ara toplam
        sub_row = QHBoxLayout()
        sub_l = QLabel("Ara Toplam")
        sub_l.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        self._subtotal_lbl = QLabel("₺ 0,00")
        self._subtotal_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._subtotal_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600;"
        )
        sub_row.addWidget(sub_l)
        sub_row.addStretch()
        sub_row.addWidget(self._subtotal_lbl)
        b_lay.addLayout(sub_row)

        # Kargo
        ship_row = QHBoxLayout()
        ship_l = QLabel("Kargo / Sigortalı Teslimat")
        ship_l.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        self._shipping_lbl = QLabel("₺ 0,00")
        self._shipping_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._shipping_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600;"
        )
        ship_row.addWidget(ship_l)
        ship_row.addStretch()
        ship_row.addWidget(self._shipping_lbl)
        b_lay.addLayout(ship_row)

        # Ücretsiz kargo bilgisi
        self._free_hint = QLabel("")
        self._free_hint.setStyleSheet(
            f"color: {Colors.GREEN}; font-size: 10px; font-weight: 600;"
        )
        b_lay.addWidget(self._free_hint)

        # Ayraç
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Colors.BORDER_DEFAULT};")
        b_lay.addWidget(sep)

        # Genel toplam + Ödemeye Geç
        grand_row = QHBoxLayout()
        grand_row.setSpacing(14)
        g_l = QLabel("Genel Toplam")
        g_l.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700;"
        )
        self._total_lbl = QLabel("₺ 0,00")
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self._total_lbl.setStyleSheet(
            f"color: {Colors.GOLD_BRIGHT}; font-size: 24px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY};"
        )
        grand_row.addWidget(g_l)
        grand_row.addSpacing(6)
        grand_row.addWidget(self._total_lbl)
        grand_row.addStretch()

        self._btn_order = QPushButton("  Ödemeye Geç  →")
        self._btn_order.setFixedHeight(46)
        self._btn_order.setFixedWidth(210)
        self._btn_order.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_order.setStyleSheet(gold_btn())
        self._btn_order.clicked.connect(self._go_checkout)
        grand_row.addWidget(self._btn_order)
        b_lay.addLayout(grand_row)

        root.addWidget(bottom)

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return

        items = self._ctx.cart_service.get_cart_items(user.id)

        # Önceki satırları temizle
        for row in self._rows:
            row.setParent(None)
            row.deleteLater()
        self._rows.clear()

        if not items:
            self._empty_lbl.show()
            self._count_lbl.setText("0 ürün")
            self._update_summary(0.0)
            self._btn_order.setEnabled(False)
            self.cart_changed.emit()
            return

        self._empty_lbl.hide()
        self._btn_order.setEnabled(True)

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        subtotal = 0.0
        total_qty = 0

        for it in items:
            unit = self._ctx.price_calculator.calculate(it["product"], gold)
            row  = _CartRow(
                it, unit,
                on_qty_change=self._on_qty_change,
                on_remove=self._on_remove,
            )
            self._list_lay.addWidget(row)
            self._rows.append(row)
            subtotal  += unit * it["quantity"]
            total_qty += it["quantity"]

        self._count_lbl.setText(f"{total_qty} ürün")
        self._update_summary(subtotal)
        self.cart_changed.emit()

    # ── Aksiyonlar ────────────────────────────────────────────

    def _on_qty_change(self, product_id: int, new_qty: int) -> None:
        user = self._ctx.auth_service.get_current_user()
        self._ctx.cart_service.update_quantity(user.id, product_id, new_qty)
        self._recalculate_total()

    def _on_remove(self, product_id: int, name: str) -> None:
        user = self._ctx.auth_service.get_current_user()
        self._ctx.cart_service.remove_from_cart(user.id, product_id)
        Toast.show_info(self, f"{name} sepetten çıkarıldı")
        self.refresh()

    def _recalculate_total(self) -> None:
        user  = self._ctx.auth_service.get_current_user()
        items = self._ctx.cart_service.get_cart_items(user.id)
        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        subtotal = 0.0
        total_qty = 0
        for it in items:
            unit = self._ctx.price_calculator.calculate(it["product"], gold)
            subtotal  += unit * it["quantity"]
            total_qty += it["quantity"]
        self._count_lbl.setText(f"{total_qty} ürün")
        self._update_summary(subtotal)
        self.cart_changed.emit()

    def _update_summary(self, subtotal: float) -> None:
        """Ara toplam, kargo, genel toplam etiketlerini günceller."""
        shipping = calculate_shipping(subtotal)
        total    = subtotal + shipping
        self._subtotal_lbl.setText(f"₺ {subtotal:,.2f}")
        if shipping > 0:
            self._shipping_lbl.setText(f"₺ {shipping:,.2f}")
            remaining = SHIPPING_FREE_THRESHOLD - subtotal
            self._free_hint.setText(
                f"₺ {remaining:,.0f} daha alın → ücretsiz sigortalı teslimat"
            )
            self._free_hint.show()
        elif subtotal > 0:
            self._shipping_lbl.setText("Ücretsiz")
            self._free_hint.setText("✓ Sigortalı teslimat ücretsiz")
            self._free_hint.show()
        else:
            self._shipping_lbl.setText("—")
            self._free_hint.setText("")
            self._free_hint.hide()
        self._total_lbl.setText(f"₺ {total:,.2f}")

    def _go_checkout(self) -> None:
        """Sepet doluysa ödeme sayfasına yönlendir (UserWindow yakalayacak)."""
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return
        items = self._ctx.cart_service.get_cart_items(user.id)
        if not items:
            Toast.show_info(self, "Sepetiniz boş")
            return
        self.checkout_requested.emit()
