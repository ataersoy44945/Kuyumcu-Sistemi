from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QDoubleSpinBox, QSpinBox, QCheckBox, QTextEdit,
    QFileDialog,
)

from backend.app_context import AppContext
from backend.models.product import Product
from config import KARAT_COEFFICIENTS
from frontend.styles.app_theme import Colors, Radius, gold_button_style, input_style


class ProductDialog(QDialog):
    """Ürün ekle veya düzenle diyalogu."""

    def __init__(self, ctx: AppContext, product: Product = None, parent=None):
        super().__init__(parent)
        self._ctx     = ctx
        self._product = product          # None → ekle, dolu → düzenle
        self._image_path: str = ""

        self.setWindowTitle("Ürün Düzenle" if product else "Yeni Ürün Ekle")
        self.setFixedSize(560, 680)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {Colors.BG_CARD}; }}")
        self._build_ui()
        if product:
            self._populate(product)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Ürün Düzenle" if self._product else "Yeni Ürün Ekle")
        title.setStyleSheet(f"color: {Colors.GOLD_PRIMARY}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        # Ürün Adı
        grid.addWidget(self._lbl("Ürün Adı *"), 0, 0, 1, 2)
        self._name = QLineEdit()
        self._name.setFixedHeight(38)
        self._name.setStyleSheet(input_style())
        grid.addWidget(self._name, 1, 0, 1, 2)

        # Kategori
        grid.addWidget(self._lbl("Kategori *"), 2, 0)
        self._category = QComboBox()
        self._category.setFixedHeight(38)
        self._category.setStyleSheet(input_style())
        cats = self._ctx.product_service.get_categories()
        for c in cats:
            self._category.addItem(c.name, c.id)
        grid.addWidget(self._category, 3, 0)

        # Ayar
        grid.addWidget(self._lbl("Ayar *"), 2, 1)
        self._karat = QComboBox()
        self._karat.setFixedHeight(38)
        self._karat.setStyleSheet(input_style())
        for k in KARAT_COEFFICIENTS:
            self._karat.addItem(f"{k} Ayar", k)
        grid.addWidget(self._karat, 3, 1)

        # Gram
        grid.addWidget(self._lbl("Gram *"), 4, 0)
        self._gram = QDoubleSpinBox()
        self._gram.setRange(0.01, 9999.99)
        self._gram.setDecimals(2)
        self._gram.setSuffix(" gr")
        self._gram.setFixedHeight(38)
        self._gram.setStyleSheet(input_style())
        grid.addWidget(self._gram, 5, 0)

        # İşçilik
        grid.addWidget(self._lbl("İşçilik Ücreti (₺)"), 4, 1)
        self._labor = QDoubleSpinBox()
        self._labor.setRange(0, 99999)
        self._labor.setDecimals(2)
        self._labor.setFixedHeight(38)
        self._labor.setStyleSheet(input_style())
        grid.addWidget(self._labor, 5, 1)

        # Kar marjı
        grid.addWidget(self._lbl("Kar Marjı (%)"), 6, 0)
        self._margin = QDoubleSpinBox()
        self._margin.setRange(0, 100)
        self._margin.setDecimals(1)
        self._margin.setValue(15.0)
        self._margin.setFixedHeight(38)
        self._margin.setStyleSheet(input_style())
        grid.addWidget(self._margin, 7, 0)

        # Stok
        grid.addWidget(self._lbl("Stok Adedi"), 6, 1)
        self._stock = QSpinBox()
        self._stock.setRange(0, 9999)
        self._stock.setFixedHeight(38)
        self._stock.setStyleSheet(input_style())
        grid.addWidget(self._stock, 7, 1)

        # Açıklama
        grid.addWidget(self._lbl("Açıklama"), 8, 0, 1, 2)
        self._desc = QTextEdit()
        self._desc.setFixedHeight(70)
        self._desc.setStyleSheet(input_style())
        grid.addWidget(self._desc, 9, 0, 1, 2)

        # Görsel
        img_row = QHBoxLayout()
        self._img_path_lbl = QLabel("Görsel seçilmedi")
        self._img_path_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        btn_img = QPushButton("Görsel Seç")
        btn_img.setFixedHeight(32)
        btn_img.setStyleSheet(f"""
            QPushButton {{ background: {Colors.BG_ELEVATED}; color: {Colors.GOLD_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: {Radius.SM}; padding: 0 12px; }}
            QPushButton:hover {{ border-color: {Colors.GOLD_PRIMARY}; }}
        """)
        btn_img.clicked.connect(self._pick_image)
        img_row.addWidget(self._img_path_lbl)
        img_row.addWidget(btn_img)
        grid.addWidget(self._lbl("Ürün Görseli"), 10, 0, 1, 2)
        grid.addLayout(img_row, 11, 0, 1, 2)

        # Satışta mı
        self._for_sale = QCheckBox("Satışta")
        self._for_sale.setChecked(True)
        self._for_sale.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        grid.addWidget(self._for_sale, 12, 0)

        layout.addLayout(grid)

        # Hata etiketi
        self._error_lbl = QLabel("")
        self._error_lbl.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px;")
        self._error_lbl.hide()
        layout.addWidget(self._error_lbl)

        layout.addStretch()

        # Butonlar
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("İptal")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER}; border-radius: {Radius.SM}; padding: 0 20px; }}
            QPushButton:hover {{ border-color: {Colors.GOLD_PRIMARY}; color: {Colors.GOLD_PRIMARY}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Kaydet")
        btn_save.setFixedHeight(40)
        btn_save.setStyleSheet(gold_button_style())
        btn_save.clicked.connect(self._on_save)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    # ── Private ───────────────────────────────────────────────

    def _lbl(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; font-weight: 600;")
        return l

    def _pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Görsel Seç", "", "Görseller (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._image_path = path
            import os
            self._img_path_lbl.setText(os.path.basename(path))

    def _populate(self, p: Product) -> None:
        self._name.setText(p.name)
        idx = self._category.findData(p.category_id)
        if idx >= 0:
            self._category.setCurrentIndex(idx)
        idx = self._karat.findData(p.karat)
        if idx >= 0:
            self._karat.setCurrentIndex(idx)
        self._gram.setValue(p.weight_grams)
        self._labor.setValue(p.labor_cost)
        self._margin.setValue(p.profit_margin)
        self._stock.setValue(p.stock_quantity)
        self._desc.setText(p.description or "")
        self._for_sale.setChecked(p.is_for_sale)
        if p.image_path:
            self._image_path = p.image_path
            import os
            self._img_path_lbl.setText(os.path.basename(p.image_path))

    def _on_save(self) -> None:
        from backend.utils.validators import ValidationError
        try:
            user = self._ctx.auth_service.get_current_user()
            data = {
                "name":          self._name.text().strip(),
                "category_id":   self._category.currentData(),
                "karat":         self._karat.currentData(),
                "weight_grams":  self._gram.value(),
                "labor_cost":    self._labor.value(),
                "profit_margin": self._margin.value(),
                "stock_quantity": self._stock.value(),
                "description":   self._desc.toPlainText(),
                "image_path":    self._image_path or None,
                "is_for_sale":   self._for_sale.isChecked(),
                "use_calculated_price": True,
            }
            if not data["name"]:
                raise ValidationError("Ürün adı boş olamaz.")

            if self._product:
                self._ctx.product_service.update_product(self._product.id, data)
            else:
                self._ctx.product_service.add_product(data, admin_id=user.id)

            self._error_lbl.hide()
            self.accept()

        except (ValidationError, ValueError) as e:
            self._error_lbl.setText(str(e))
            self._error_lbl.show()
        except Exception as e:
            self._error_lbl.setText(f"Hata: {e}")
            self._error_lbl.show()
