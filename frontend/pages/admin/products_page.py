from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from frontend.styles.app_theme import (
    Colors, Radius, gold_btn, input_field, premium_table,
)
from frontend.dialogs.product_dialog import ProductDialog
from frontend.dialogs.confirm_dialog import ConfirmDialog


class ProductsPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._all_products = []
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(16)

        # ── Üst araç çubuğu ───────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Ürün adı ile ara…")
        self._search.setFixedHeight(40)
        self._search.setStyleSheet(input_field())
        self._search.textChanged.connect(self._filter)

        self._cat_filter = QComboBox()
        self._cat_filter.setFixedHeight(40)
        self._cat_filter.setFixedWidth(170)
        self._cat_filter.setStyleSheet(input_field())
        self._cat_filter.currentIndexChanged.connect(self._filter)

        btn_add = QPushButton("  +  Yeni Ürün")
        btn_add.setFixedHeight(40)
        btn_add.setStyleSheet(gold_btn())
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_product)

        top.addWidget(self._search)
        top.addWidget(self._cat_filter)
        top.addStretch()
        top.addWidget(btn_add)
        lay.addLayout(top)

        # ── Tablo ─────────────────────────────────────────────
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Ürün Adı", "Kategori", "Ayar", "Gram", "Stok", "İşlemler"]
        )
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 48)
        self._table.setColumnWidth(6, 170)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(premium_table() + f"""
            QTableWidget {{ background: {Colors.BG_SURFACE}; border-radius: {Radius.LG}; }}
            QHeaderView::section {{ padding: 10px 14px; }}
            QTableWidget::item:alternate {{ background: rgba(25,36,64,0.4); }}
        """)
        lay.addWidget(self._table)

        # ── Boş durum etiketi ─────────────────────────────────
        self._empty_lbl = QLabel("📦  Henüz ürün eklenmedi\n\nİlk ürününüzü eklemek için '+ Yeni Ürün' butonunu kullanın.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; "
            f"padding: 60px; background: transparent;"
        )
        self._empty_lbl.setVisible(False)
        lay.addWidget(self._empty_lbl)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px;"
        )
        lay.addWidget(self._count_lbl)

    def refresh(self) -> None:
        self._all_products = self._ctx.product_service.get_all(for_sale_only=False)
        self._cat_filter.blockSignals(True)
        self._cat_filter.clear()
        self._cat_filter.addItem("Tüm Kategoriler", None)
        for c in self._ctx.product_service.get_categories(active_only=False):
            self._cat_filter.addItem(c.name, c.id)
        self._cat_filter.blockSignals(False)
        self._filter()

    def _filter(self) -> None:
        query  = self._search.text().strip().lower()
        cat_id = self._cat_filter.currentData()
        filtered = [
            p for p in self._all_products
            if (not query or query in p.name.lower())
            and (cat_id is None or p.category_id == cat_id)
        ]
        self._populate_table(filtered)

    def _populate_table(self, products: list) -> None:
        has = bool(products)
        self._table.setVisible(has)
        self._empty_lbl.setVisible(not has)
        if not has:
            self._count_lbl.setText("Ürün bulunamadı")
            return

        self._table.setRowCount(len(products))
        for r, p in enumerate(products):
            self._table.setRowHeight(r, 56)
            self._table.setItem(r, 0, self._cell(str(p.id), Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(r, 1, self._cell(p.name))
            self._table.setItem(r, 2, self._cell(p.category_name or "—"))
            self._table.setItem(r, 3, self._cell(f"{p.karat} Ayar", Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(r, 4, self._cell(f"{p.weight_grams:.2f} gr", Qt.AlignmentFlag.AlignCenter))

            stock = QTableWidgetItem(str(p.stock_quantity))
            stock.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            if p.stock_quantity == 0:
                stock.setForeground(QColor(Colors.RED))
            elif p.stock_quantity <= 3:
                stock.setForeground(QColor(Colors.AMBER))
            else:
                stock.setForeground(QColor(Colors.GREEN))
            self._table.setItem(r, 5, stock)

            # İşlem butonları
            btn_w = QWidget()
            btn_lay = QHBoxLayout(btn_w)
            btn_lay.setContentsMargins(6, 8, 6, 8)
            btn_lay.setSpacing(6)

            btn_edit = QPushButton("Düzenle")
            btn_edit.setFixedSize(86, 36)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(self._text_btn("#3B82F6", "#1E3A8A"))
            btn_edit.clicked.connect(lambda _, prod=p: self._edit_product(prod))

            btn_del = QPushButton("Sil")
            btn_del.setFixedSize(64, 36)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(self._text_btn("#EF4444", "#7F1D1D"))
            btn_del.clicked.connect(lambda _, prod=p: self._delete_product(prod))

            btn_lay.addWidget(btn_edit)
            btn_lay.addWidget(btn_del)
            self._table.setCellWidget(r, 6, btn_w)

        self._count_lbl.setText(f"{len(products)} ürün listeleniyor")

    def _add_product(self) -> None:
        if ProductDialog(self._ctx, parent=self).exec():
            self.refresh()

    def _edit_product(self, product) -> None:
        if ProductDialog(self._ctx, product=product, parent=self).exec():
            self.refresh()

    def _delete_product(self, product) -> None:
        if ConfirmDialog.ask(self, "Ürün Sil",
                             f'"{product.name}" silinsin mi? Bu işlem geri alınamaz.'):
            self._ctx.product_service.delete_product(product.id)
            self.refresh()

    @staticmethod
    def _cell(text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
              ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(align))
        return item

    @staticmethod
    def _text_btn(color: str, deep: str) -> str:
        """Solid arka planlı belirgin buton."""
        return f"""
            QPushButton {{
                background: {deep};
                color: #FFFFFF;
                border: 1px solid {color};
                border-radius: 6px;
                font-size: 12px; font-weight: 600;
                padding: 0 8px;
            }}
            QPushButton:hover {{
                background: {color};
                border-color: {color};
            }}
            QPushButton:pressed {{
                background: {deep};
            }}
        """
