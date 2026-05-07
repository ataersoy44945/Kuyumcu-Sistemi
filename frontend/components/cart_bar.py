"""
CartBar — Tüm kullanıcı sayfalarının altında sabit duran sepet özet barı.

Sepette ürün varsa görünür; yoksa gizlenir. UserWindow tarafından bir kez
oluşturulur ve sayfalar arasında durumu korunur.

Sinyaller:
    view_cart_clicked  → kullanıcı "Sepeti Gör" butonuna bastı
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from frontend.styles.app_theme import Colors, Fonts, Radius


class CartBar(QFrame):
    """Sticky alt sepet barı — premium koyu lacivert + altın çizgi."""

    view_cart_clicked = pyqtSignal()

    BAR_HEIGHT = 76

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self._total = 0.0
        self.setFixedHeight(self.BAR_HEIGHT)
        # Kendi pencere başlığı/arka planı yok — pencerenin alt şeridi
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._build_ui()
        self._apply_style()
        self.hide()  # Sepet boşsa görünmesin

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 12, 28, 12)
        lay.setSpacing(18)

        # Sepet ikonu rozeti
        self._icon_lbl = QLabel("🛒")
        self._icon_lbl.setFixedSize(46, 46)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD_DIM});
            color: {Colors.TEXT_ON_GOLD};
            border-radius: 23px;
            font-size: 20px;
            border: none;
        """)
        lay.addWidget(self._icon_lbl)

        # Sol metin sütunu: "Sepetinizde X ürün var"
        col = QVBoxLayout()
        col.setSpacing(2)

        self._count_lbl = QLabel("Sepetinizde 0 ürün var")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        self._sub_lbl = QLabel("Siparişinizi tamamlamak için sepete gidin")
        self._sub_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        col.addWidget(self._count_lbl)
        col.addWidget(self._sub_lbl)
        lay.addLayout(col)

        lay.addStretch()

        # Toplam fiyat
        total_col = QVBoxLayout()
        total_col.setSpacing(2)
        total_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        t_cap = QLabel("TOPLAM")
        t_cap.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )
        t_cap.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._total_lbl = QLabel("₺ 0,00")
        self._total_lbl.setStyleSheet(
            f"color: {Colors.GOLD_BRIGHT}; font-size: 20px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY}; background: transparent; border: none;"
        )
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_col.addWidget(t_cap)
        total_col.addWidget(self._total_lbl)
        lay.addLayout(total_col)

        lay.addSpacing(8)

        # Sepeti Gör butonu
        self._view_btn = QPushButton("  Sepeti Gör  →")
        self._view_btn.setFixedHeight(46)
        self._view_btn.setMinimumWidth(160)
        self._view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});
                color: {Colors.TEXT_ON_GOLD};
                border: none; border-radius: {Radius.MD};
                padding: 0 22px;
                font-size: 13px; font-weight: 800; letter-spacing: 0.4px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #FFD700, stop:1 {Colors.GOLD_BRIGHT});
            }}
            QPushButton:pressed {{ background: {Colors.GOLD_DIM}; }}
        """)
        self._view_btn.clicked.connect(self.view_cart_clicked.emit)
        lay.addWidget(self._view_btn)

    def _apply_style(self) -> None:
        # Üstte altın çizgi, koyu zemin, üst köşelerde hafif yuvarlama
        self.setStyleSheet(f"""
            CartBar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {Colors.BG_RAISED}, stop:1 {Colors.BG_BASE});
                border-top: 2px solid {Colors.GOLD};
            }}
        """)
        # Yukarı doğru yumuşak gölge
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, -4)
        self.setGraphicsEffect(shadow)

    # ── Public API ───────────────────────────────────────────

    def update_state(self, count: int, total: float) -> None:
        """Sepet adedini ve toplamı yeniler. Boşsa kendini gizler."""
        self._count = max(0, int(count))
        self._total = max(0.0, float(total))

        if self._count <= 0:
            self.hide()
            return

        unit = "ürün" if self._count == 1 else "ürün"
        self._count_lbl.setText(f"Sepetinizde {self._count} {unit} var")
        self._total_lbl.setText(f"₺ {self._total:,.2f}")
        self.show()
