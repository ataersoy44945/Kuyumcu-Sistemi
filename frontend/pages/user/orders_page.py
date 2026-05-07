"""
Kullanıcının siparişlerini listeleyen sayfa.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from backend.models.order import Order
from frontend.styles.app_theme import Colors, Fonts, Radius


_STATUS_COLORS = {
    "pending":    Colors.AMBER,
    "processing": Colors.BLUE,
    "completed":  Colors.GREEN,
    "cancelled":  Colors.RED,
}


class OrdersPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._cards: list[QWidget] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # Başlık
        head = QHBoxLayout()
        title = QLabel("📋  Siparişlerim")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 20px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        head.addWidget(title)
        head.addSpacing(12)
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 12px; font-weight: 700; "
            f"border: 1px solid {Colors.GOLD}55; border-radius: {Radius.FULL}; "
            f"padding: 5px 12px; background: {Colors.GOLD_SUBTLE};"
        )
        head.addWidget(self._count_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        head.addStretch()
        root.addLayout(head)

        # Liste
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(10)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_w)
        root.addWidget(self._scroll, 1)

        # Boş durum
        self._empty_lbl = QLabel(
            "📋\nHenüz hiç siparişiniz yok.\nÜrünler sayfasından alışverişe başlayabilirsiniz."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 80px; "
            f"background: transparent;"
        )
        self._empty_lbl.hide()
        root.addWidget(self._empty_lbl)

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return

        orders = self._ctx.order_service.get_user_orders(user.id)

        # Önceki kartları temizle
        for c in self._cards:
            c.setParent(None)
            c.deleteLater()
        self._cards.clear()

        if not orders:
            self._empty_lbl.show()
            self._scroll.hide()
            self._count_lbl.setText("0 sipariş")
            return

        self._empty_lbl.hide()
        self._scroll.show()
        self._count_lbl.setText(f"{len(orders)} sipariş")

        for o in orders:
            card = self._build_order_card(o)
            self._list_lay.addWidget(card)
            self._cards.append(card)

    # ── Kart oluştur ──────────────────────────────────────────

    def _build_order_card(self, order: Order) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.LG};
            }}
            QFrame:hover {{
                border-color: {Colors.GOLD}55;
                background: {Colors.BG_ELEVATED};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(20)

        # Sol: sipariş no + tarih
        col1 = QVBoxLayout()
        col1.setSpacing(3)
        num = QLabel(order.order_number or f"#{order.id}")
        num.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 14px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY_M}; letter-spacing: 0.4px;"
        )
        date = QLabel(order.created_at or "—")
        date.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        col1.addWidget(num)
        col1.addWidget(date)
        lay.addLayout(col1, 0)

        lay.addSpacing(10)

        # Orta: ürün özeti
        col2 = QVBoxLayout()
        col2.setSpacing(3)
        item_count = sum(it.quantity for it in order.items)
        names = ", ".join(
            (it.product_name or f"#{it.product_id}") for it in order.items[:3]
        )
        if len(order.items) > 3:
            names += "…"
        items_lbl = QLabel(f"{item_count} ürün")
        items_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700;"
        )
        names_lbl = QLabel(names or "—")
        names_lbl.setStyleSheet(f"color: {Colors.TEXT_BODY}; font-size: 11px;")
        names_lbl.setWordWrap(True)
        col2.addWidget(items_lbl)
        col2.addWidget(names_lbl)
        lay.addLayout(col2, 1)

        # Sağ: ödeme yöntemi + durum + tutar
        col3 = QVBoxLayout()
        col3.setSpacing(4)
        col3.setAlignment(Qt.AlignmentFlag.AlignRight)

        pm = QLabel(order.payment_method_label())
        pm.setAlignment(Qt.AlignmentFlag.AlignRight)
        pm.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 600;")

        status_color = _STATUS_COLORS.get(order.status, Colors.TEXT_MUTED)
        st = QLabel(f"●  {order.status_label()}")
        st.setAlignment(Qt.AlignmentFlag.AlignRight)
        st.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 700;")

        total = QLabel(f"₺ {order.total_amount:,.2f}")
        total.setAlignment(Qt.AlignmentFlag.AlignRight)
        total.setStyleSheet(
            f"color: {Colors.GOLD_BRIGHT}; font-size: 17px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY};"
        )

        col3.addWidget(pm)
        col3.addWidget(st)
        col3.addWidget(total)
        lay.addLayout(col3, 0)

        return card
