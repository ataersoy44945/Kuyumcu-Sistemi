from pathlib import Path

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QCursor

import config
from backend.models.product import Product
from frontend.styles.app_theme import Colors, Radius


class ProductCard(QFrame):
    """
    Kullanıcı panelinde ürünleri kart olarak gösteren bileşen.
    Favori toggle, sepete ekle ve detay sinyalleri emit eder.
    """

    favorite_toggled = pyqtSignal(int, bool)   # product_id, is_now_favorite
    cart_requested   = pyqtSignal(int)          # product_id
    detail_requested = pyqtSignal(int)          # product_id

    def __init__(
        self,
        product: Product,
        price: float,
        is_favorite: bool = False,
        show_favorite_btn: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._product  = product
        self._price    = price
        self._is_fav   = is_favorite
        self._show_fav = show_favorite_btn

        self.setFixedWidth(210)
        self.setMinimumHeight(320)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._set_style(hovered=False)
        self._build_ui()

    # ── UI inşa ───────────────────────────────────────────────

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 14)
        lay.setSpacing(6)

        # Görsel alanı
        self._img_lbl = QLabel()
        self._img_lbl.setFixedHeight(148)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            f"background: {Colors.BG_ELEVATED}; border-radius: {Radius.MD}; border: none;"
        )
        self._load_image()
        lay.addWidget(self._img_lbl)

        # Ürün adı
        name_lbl = QLabel(self._product.name)
        name_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600; border: none;"
        )
        name_lbl.setWordWrap(True)
        name_lbl.setMaximumWidth(186)
        lay.addWidget(name_lbl)

        # Meta — kategori · ayar
        cat = self._product.category_name or ""
        meta = QLabel(f"{cat}  ·  {self._product.karat} Ayar")
        meta.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;")
        lay.addWidget(meta)

        # Gram
        gram = QLabel(f"⚖️  {self._product.weight_grams:.2f} gr")
        gram.setStyleSheet(f"color: {Colors.TEXT_BODY}; font-size: 11px; border: none;")
        lay.addWidget(gram)

        # Fiyat
        price_lbl = QLabel(f"₺ {self._price:,.0f}")
        price_lbl.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 17px; font-weight: 700; border: none;"
        )
        lay.addWidget(price_lbl)

        lay.addStretch()

        # ── Alt buton satırı ──────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        # Favori butonu
        if self._show_fav:
            self._fav_btn = self._make_fav_btn()
            self._fav_btn.clicked.connect(self._toggle_fav)
            btn_row.addWidget(self._fav_btn)

        # Sepet butonu
        cart_btn = QPushButton("🛒")
        cart_btn.setFixedSize(34, 34)
        cart_btn.setToolTip("Sepete Ekle")
        cart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cart_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.BLUE};
                border: 1px solid {Colors.BLUE}44; border-radius: 17px; font-size: 15px;
            }}
            QPushButton:hover {{
                background: {Colors.BLUE_BG}; border-color: {Colors.BLUE};
            }}
        """)
        cart_btn.clicked.connect(lambda: self.cart_requested.emit(self._product.id))
        btn_row.addWidget(cart_btn)

        btn_row.addStretch()

        # Detay linki
        detail_btn = QPushButton("İncele →")
        detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        detail_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.GOLD};
                border: none; font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {Colors.GOLD_LIGHT}; }}
        """)
        detail_btn.clicked.connect(
            lambda: self.detail_requested.emit(self._product.id)
        )
        btn_row.addWidget(detail_btn)

        lay.addLayout(btn_row)

    # ── Görsel yükleme ────────────────────────────────────────

    def _load_image(self) -> None:
        raw = self._product.image_path if hasattr(self._product, "image_path") else None
        resolved: Path | None = None
        if raw:
            p = Path(raw)
            # Göreceli yolsa proje köküne göre çöz
            resolved = p if p.is_absolute() else config.BASE_DIR / p
            # Son çare: sadece dosya adını ürün görselleri klasöründe ara
            if not resolved.exists():
                resolved = config.PRODUCT_IMAGES_DIR / p.name

        if resolved and resolved.exists():
            pix = QPixmap(str(resolved)).scaled(
                186, 144,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_lbl.setPixmap(pix)
        else:
            from frontend.utils import category_icon
            self._img_lbl.setText(category_icon(self._product.category_name or ""))
            self._img_lbl.setStyleSheet(
                f"background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                f"  stop:0 {Colors.BG_ELEVATED}, stop:1 {Colors.BG_RAISED});"
                f"font-size: 54px; border-radius: {Radius.MD}; border: none;"
            )

    # ── Favori butonu ─────────────────────────────────────────

    def _make_fav_btn(self) -> QPushButton:
        btn = QPushButton("♥" if self._is_fav else "♡")
        btn.setFixedSize(34, 34)
        color = "#E53935" if self._is_fav else Colors.TEXT_MUTED
        btn.setStyleSheet(self._fav_style(color))
        return btn

    def _fav_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                color: {color}; background: transparent;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 17px; font-size: 15px;
            }}
            QPushButton:hover {{ border-color: #E53935; color: #E53935; }}
        """

    def _toggle_fav(self) -> None:
        self._is_fav = not self._is_fav
        self._fav_btn.setText("♥" if self._is_fav else "♡")
        color = "#E53935" if self._is_fav else Colors.TEXT_MUTED
        self._fav_btn.setStyleSheet(self._fav_style(color))
        self.favorite_toggled.emit(self._product.id, self._is_fav)

    # ── Hover glow efekti ─────────────────────────────────────

    def _set_style(self, hovered: bool) -> None:
        if hovered:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG_SURFACE};
                    border: 1px solid {Colors.GOLD}80;
                    border-radius: {Radius.LG};
                    border-top: 2px solid {Colors.GOLD};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.BG_SURFACE};
                    border: 1px solid {Colors.BORDER_DIM};
                    border-radius: {Radius.LG};
                }}
            """)

    def enterEvent(self, event):
        self._set_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_style(False)
        super().leaveEvent(event)
