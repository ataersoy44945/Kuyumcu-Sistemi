from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Fonts, Radius, premium_table


class StatCard(QFrame):
    """Tek bir istatistik metriğini gösteren premium kart."""

    def __init__(self, icon: str, label: str, value: str, color: str = None):
        super().__init__()
        color = color or Colors.GOLD
        self.setFixedHeight(124)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-radius: {Radius.LG};
                border-left: 4px solid {color};
            }}
            QFrame:hover {{
                background: {Colors.BG_ELEVATED};
                border-color: {color}60;
                border-left-color: {color};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        top = QHBoxLayout()
        ico = QLabel(icon)
        ico.setStyleSheet(
            "font-size: 22px; background: transparent; border: none;"
        )
        top.addWidget(ico)
        top.addStretch()
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.8px; background: transparent; border: none;"
        )
        top.addWidget(lbl)
        lay.addLayout(top)

        val = QLabel(value)
        val.setStyleSheet(
            f"color: {color}; font-size: 32px; font-weight: 700; "
            f"background: transparent; border: none; font-family: {Fonts.FAMILY};"
        )
        val.setObjectName("value")
        lay.addWidget(val)

    def set_value(self, value: str) -> None:
        self.findChild(QLabel, "value").setText(value)


class _SectionFrame(QFrame):
    """Başlık + içerik içeren tutarlı bölüm kartı."""

    def __init__(self, title: str, title_color: str = None):
        super().__init__()
        title_color = title_color or Colors.TEXT_H1
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-radius: {Radius.LG};
            }}
        """)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 16, 20, 16)
        self._lay.setSpacing(12)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {title_color}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        self._lay.addWidget(title_lbl)

    def body_layout(self) -> QVBoxLayout:
        return self._lay


def _make_table(cols: int, headers: list[str]) -> QTableWidget:
    tbl = QTableWidget(0, cols)
    tbl.setHorizontalHeaderLabels(headers)
    tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(False)
    tbl.setAlternatingRowColors(True)
    tbl.setStyleSheet(premium_table() + f"""
        QTableWidget {{ background: transparent; border: none; }}
        QHeaderView::section {{
            background: {Colors.BG_RAISED}; color: {Colors.TEXT_MUTED};
            border: none; border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            padding: 8px 12px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
        }}
        QTableWidget::item {{ padding: 9px 12px; border: none; }}
        QTableWidget::item:alternate {{ background: rgba(25,36,64,0.4); }}
    """)
    return tbl


class DashboardPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

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
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(20)

        # ── Stat kartları ─────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self._sc_users    = StatCard("👥", "Toplam Müşteri",    "—", Colors.BLUE)
        self._sc_products = StatCard("📦", "Toplam Ürün",       "—", Colors.GOLD)
        self._sc_instock  = StatCard("✅", "Stokta",            "—", Colors.GREEN)
        self._sc_orders   = StatCard("📋", "Bekleyen Sipariş",  "—", Colors.AMBER)
        for sc in (self._sc_users, self._sc_products, self._sc_instock, self._sc_orders):
            stats_row.addWidget(sc)
        lay.addLayout(stats_row)

        # ── Alt bölüm: Favoriler + Kritik Stok ───────────────
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        bottom.addWidget(self._build_top_favorites(), 3)
        bottom.addWidget(self._build_low_stock(), 2)
        lay.addLayout(bottom)

        # ── Son siparişler ────────────────────────────────────
        lay.addWidget(self._build_recent_orders())
        lay.addStretch()

    # ── Favoriler bölümü ──────────────────────────────────────

    def _build_top_favorites(self) -> QFrame:
        frame = _SectionFrame("⭐  En Çok Favorilenen Ürünler")
        self._fav_table = _make_table(3, ["Ürün Adı", "Kategori", "❤️"])
        h = self._fav_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._fav_table.setColumnWidth(2, 52)
        frame.body_layout().addWidget(self._fav_table)
        return frame

    # ── Kritik stok bölümü ────────────────────────────────────

    def _build_low_stock(self) -> QFrame:
        frame = _SectionFrame("⚠️  Kritik Stok Uyarıları", Colors.AMBER)
        self._stock_table = _make_table(2, ["Ürün", "Stok"])
        h = self._stock_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._stock_table.setColumnWidth(1, 60)
        frame.body_layout().addWidget(self._stock_table)
        return frame

    # ── Son siparişler bölümü ─────────────────────────────────

    def _build_recent_orders(self) -> QFrame:
        frame = _SectionFrame("📋  Son Siparişler")
        self._orders_table = _make_table(
            5, ["Sipariş #", "Müşteri", "Tutar", "Durum", "Tarih"]
        )
        h = self._orders_table.horizontalHeader()
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._orders_table.setColumnWidth(0, 80)
        self._orders_table.setFixedHeight(220)
        frame.body_layout().addWidget(self._orders_table)
        return frame

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        self._sc_users.set_value(str(self._ctx.user_repo.count()))
        stats = self._ctx.product_service.get_statistics()
        self._sc_products.set_value(str(stats["total"]))
        self._sc_instock.set_value(str(stats["in_stock"]))
        counts = self._ctx.order_service.get_dashboard_counts()
        self._sc_orders.set_value(str(counts["pending"]))

        favs = self._ctx.product_service.get_most_favorited(10)
        self._fav_table.setRowCount(len(favs))
        for r, p in enumerate(favs):
            self._fav_table.setItem(r, 0, self._cell(p.name))
            self._fav_table.setItem(r, 1, self._cell(p.category_name or "—"))
            cnt = QTableWidgetItem(str(p.favorite_count))
            cnt.setForeground(QColor(Colors.GOLD))
            cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._fav_table.setItem(r, 2, cnt)

        low = self._ctx.product_service.get_low_stock()
        self._stock_table.setRowCount(len(low))
        for r, p in enumerate(low):
            self._stock_table.setItem(r, 0, self._cell(p.name))
            item = QTableWidgetItem(str(p.stock_quantity))
            item.setForeground(QColor(Colors.AMBER))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._stock_table.setItem(r, 1, item)

        status_colors = {
            "pending":    Colors.AMBER,
            "processing": Colors.BLUE,
            "completed":  Colors.GREEN,
            "cancelled":  Colors.RED,
        }
        orders = self._ctx.order_service.get_all_orders()[:10]
        self._orders_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            self._orders_table.setItem(r, 0, self._cell(f"#{o.id}"))
            self._orders_table.setItem(r, 1, self._cell(o.user_full_name or f"#{o.user_id}"))
            self._orders_table.setItem(r, 2, self._cell(f"₺ {o.total_amount:,.2f}"))
            s_item = QTableWidgetItem(o.status_label())
            s_item.setForeground(QColor(status_colors.get(o.status, Colors.TEXT_MUTED)))
            self._orders_table.setItem(r, 3, s_item)
            self._orders_table.setItem(r, 4, self._cell(o.created_at[:16]))

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        return item
