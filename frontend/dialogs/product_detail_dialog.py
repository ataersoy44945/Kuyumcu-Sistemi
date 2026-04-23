"""
ProductDetailDialog — ürün detay modalı.

Solda büyük görsel, sağda isim/kategori/ayar/gram/fiyat/stok/açıklama
ve aksiyon butonları (Sepete Ekle · Favorilere Ekle · Kapat).
Tüm sepet ve favori işlemleri AppContext üzerinden yapılır.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

import config
from backend.app_context import AppContext
from backend.models.product import Product
from frontend.styles.app_theme import Colors, Fonts, Radius
from frontend.components.toast import Toast


class ProductDetailDialog(QDialog):
    """Premium ürün detay modalı."""

    favorite_changed = pyqtSignal(int, bool)   # (product_id, is_favorite)
    added_to_cart    = pyqtSignal(int)          # product_id

    def __init__(self, ctx: AppContext, product: Product, parent=None):
        super().__init__(parent)
        self._ctx     = ctx
        self._product = product
        self._is_fav  = self._check_favorite()

        self._setup_window()
        self._build_ui()

    # ── Kurulum ───────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle(self._product.name)
        self.setModal(True)
        self.setFixedSize(880, 560)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_BASE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.LG};
            }}
        """)

    def _check_favorite(self) -> bool:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return False
        return self._ctx.favorite_service.is_favorite(user.id, self._product.id)

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_image_pane(), 5)
        root.addWidget(self._build_info_pane(), 6)

    # 1) Sol panel — büyük görsel
    def _build_image_pane(self) -> QWidget:
        pane = QFrame()
        pane.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {Colors.BG_ELEVATED},
                    stop:0.6 {Colors.BG_RAISED},
                    stop:1 rgba(212,175,55,0.12));
                border-right: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            f"background: transparent; border: none; color: {Colors.GOLD}; font-size: 110px;"
        )
        self._load_image()
        lay.addWidget(self._img_lbl, 1)

        # Kategori + ayar mini chip satırı
        meta = QHBoxLayout()
        meta.setSpacing(8)
        cat_chip = self._chip(f"◆  {self._product.category_name or '—'}", Colors.GOLD)
        karat_chip = self._chip(f"{self._product.karat} AYAR", Colors.GOLD_BRIGHT)
        meta.addWidget(cat_chip)
        meta.addWidget(karat_chip)
        meta.addStretch()
        lay.addLayout(meta)
        return pane

    def _chip(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            color: {color};
            background: rgba(8,13,24,0.55);
            border: 1px solid {color}55;
            border-radius: {Radius.FULL};
            padding: 5px 12px;
            font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
        """)
        lbl.setFixedHeight(26)
        return lbl

    def _load_image(self) -> None:
        raw = self._product.image_path
        resolved: Optional[Path] = None
        if raw:
            p = Path(raw)
            resolved = p if p.is_absolute() else config.BASE_DIR / p
            if not resolved.exists():
                alt = config.PRODUCT_IMAGES_DIR / p.name
                resolved = alt if alt.exists() else None

        if resolved and resolved.exists():
            pix = QPixmap(str(resolved)).scaled(
                360, 420,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_lbl.setPixmap(pix)
        else:
            from frontend.utils import category_icon
            self._img_lbl.setText(category_icon(self._product.category_name or ""))

    # 2) Sağ panel — bilgi + aksiyonlar
    def _build_info_pane(self) -> QWidget:
        pane = QWidget()
        pane.setStyleSheet(f"background: {Colors.BG_SURFACE};")
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(30, 28, 30, 24)
        lay.setSpacing(12)

        # Üst: başlık + kapat butonu
        top_row = QHBoxLayout()
        title = QLabel(self._product.name)
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 22px; font-weight: 700; border: none;"
        )
        title.setWordWrap(True)
        top_row.addWidget(title, 1)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_MUTED};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 16px; font-size: 14px;
            }}
            QPushButton:hover {{
                color: {Colors.RED}; border-color: {Colors.RED};
            }}
        """)
        btn_close.clicked.connect(self.reject)
        top_row.addWidget(btn_close)
        lay.addLayout(top_row)

        # Alt başlık
        subtitle = QLabel("Premium Altın Koleksiyonu")
        subtitle.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 1.5px; border: none;"
        )
        lay.addWidget(subtitle)

        # Fiyat
        price = self._calculate_price()
        price_lbl = QLabel(f"₺ {price:,.2f}")
        price_lbl.setStyleSheet(
            f"color: {Colors.GOLD_BRIGHT}; font-size: 30px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY}; border: none;"
        )
        lay.addWidget(price_lbl)

        # Ayrıntı satırları
        lay.addSpacing(6)
        lay.addWidget(self._detail_row("Kategori",    self._product.category_name or "—"))
        lay.addWidget(self._detail_row("Ayar",        f"{self._product.karat} Ayar"))
        lay.addWidget(self._detail_row("Gram",        f"{self._product.weight_grams:.2f} gr"))
        lay.addWidget(self._detail_row("İşçilik",     f"₺ {self._product.labor_cost:,.2f}"))
        lay.addWidget(self._detail_row("Stok",        self._stock_text(), self._stock_color()))

        # Açıklama
        if self._product.description:
            lay.addSpacing(8)
            desc_title = QLabel("AÇIKLAMA")
            desc_title.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                f"letter-spacing: 1.2px; border: none;"
            )
            lay.addWidget(desc_title)

            desc = QLabel(self._format_description(self._product.description))
            desc.setWordWrap(True)
            desc.setStyleSheet(
                f"color: {Colors.TEXT_BODY}; font-size: 12px; line-height: 1.4; border: none;"
            )
            lay.addWidget(desc)

        lay.addStretch()

        # Aksiyon butonları
        lay.addLayout(self._build_action_buttons())
        return pane

    def _detail_row(self, label: str, value: str,
                    value_color: str = None) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; letter-spacing: 0.3px; border: none;"
        )
        lbl.setFixedWidth(90)
        val = QLabel(value)
        val.setStyleSheet(
            f"color: {value_color or Colors.TEXT_H1}; font-size: 13px; "
            f"font-weight: 600; border: none;"
        )
        h.addWidget(lbl)
        h.addWidget(val)
        h.addStretch()
        return w

    def _format_description(self, desc: str) -> str:
        """Seed script'inden gelen '[KOD: ...]' ön-ekini ayıklayıp sadece metni gösterir."""
        lines = desc.split("\n")
        # Son satır genellikle açıklama; önceki meta satırları gizle
        return lines[-1].strip() if lines else desc

    def _stock_text(self) -> str:
        q = self._product.stock_quantity
        if q == 0:
            return "● Tükendi"
        if q <= 3:
            return f"● Son {q} adet"
        return f"● {q} adet stokta"

    def _stock_color(self) -> str:
        q = self._product.stock_quantity
        if q == 0:
            return Colors.RED
        if q <= 3:
            return Colors.AMBER
        return Colors.GREEN

    def _calculate_price(self) -> float:
        rates = self._ctx.exchange_service.get_rates()
        gold = rates.gold_gram_try if rates else 0.0
        return self._ctx.price_calculator.calculate(self._product, gold)

    # ── Butonlar ──────────────────────────────────────────────

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        # Favori toggle
        self._btn_fav = QPushButton()
        self._btn_fav.setFixedSize(48, 48)
        self._btn_fav.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_fav_button()
        self._btn_fav.clicked.connect(self._toggle_favorite)

        # Sepete ekle
        out_of_stock = self._product.stock_quantity == 0
        self._btn_cart = QPushButton(
            "  🛒  Sepete Ekle" if not out_of_stock else "  Stokta Yok"
        )
        self._btn_cart.setFixedHeight(48)
        self._btn_cart.setEnabled(not out_of_stock)
        self._btn_cart.setCursor(Qt.CursorShape.PointingHandCursor)
        if out_of_stock:
            self._btn_cart.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.BORDER_DEFAULT}; color: {Colors.TEXT_MUTED};
                    border: none; border-radius: {Radius.MD};
                    font-size: 13px; font-weight: 700; padding: 0 20px;
                }}
            """)
        else:
            self._btn_cart.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});
                    color: {Colors.TEXT_ON_GOLD};
                    border: none; border-radius: {Radius.MD};
                    font-size: 13px; font-weight: 700; padding: 0 20px;
                    letter-spacing: 0.3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FFD700, stop:1 {Colors.GOLD_BRIGHT});
                }}
            """)
        self._btn_cart.clicked.connect(self._add_to_cart)

        # Kapat
        btn_back = QPushButton("Kapat")
        btn_back.setFixedHeight(48)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD};
                font-size: 13px; padding: 0 24px;
            }}
            QPushButton:hover {{
                border-color: {Colors.GOLD}; color: {Colors.GOLD};
            }}
        """)
        btn_back.clicked.connect(self.reject)

        row.addWidget(self._btn_fav)
        row.addWidget(self._btn_cart, 1)
        row.addWidget(btn_back)
        return row

    def _update_fav_button(self) -> None:
        if self._is_fav:
            self._btn_fav.setText("♥")
            self._btn_fav.setStyleSheet("""
                QPushButton {
                    background: rgba(239,68,68,0.12);
                    color: #EF4444;
                    border: 1px solid #EF4444; border-radius: 24px;
                    font-size: 20px;
                }
                QPushButton:hover { background: rgba(239,68,68,0.20); }
            """)
        else:
            self._btn_fav.setText("♡")
            self._btn_fav.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_MUTED};
                    border: 1px solid {Colors.BORDER_DEFAULT}; border-radius: 24px;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    border-color: #EF4444; color: #EF4444;
                }}
            """)

    # ── Aksiyonlar ────────────────────────────────────────────

    def _toggle_favorite(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return
        self._ctx.favorite_service.toggle(user.id, self._product.id)
        self._is_fav = not self._is_fav
        self._update_fav_button()
        self.favorite_changed.emit(self._product.id, self._is_fav)
        msg = "Favorilere eklendi" if self._is_fav else "Favorilerden çıkarıldı"
        Toast.show_success(self, msg)

    def _add_to_cart(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return
        qty = self._ctx.cart_service.add_to_cart(user.id, self._product.id, 1)
        self.added_to_cart.emit(self._product.id)
        Toast.show_success(self, f"Sepete eklendi  (toplam {qty} adet)")
