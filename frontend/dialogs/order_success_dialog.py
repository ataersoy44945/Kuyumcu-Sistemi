"""
OrderSuccessDialog — Sipariş başarıyla oluşturulduğunda gösterilen modal.
Sipariş numarası, tarih, toplam ve "Siparişlerime Git" butonu içerir.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.models.order import Order
from frontend.styles.app_theme import Colors, Fonts, Radius, gold_btn


class OrderSuccessDialog(QDialog):

    view_orders_clicked = pyqtSignal()

    def __init__(self, order: Order, parent=None):
        super().__init__(parent)
        self._order = order
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Sipariş Tamamlandı")
        self.setModal(True)
        self.setFixedSize(520, 480)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.GOLD}55;
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 32, 36, 28)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Büyük başarı ikonu
        icon = QLabel("✓")
        icon.setFixedSize(84, 84)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GREEN}, stop:1 #15803D);
            color: white;
            font-size: 44px; font-weight: 900;
            border-radius: 42px;
            border: 3px solid {Colors.GREEN};
        """)
        wrap = QHBoxLayout()
        wrap.addStretch()
        wrap.addWidget(icon)
        wrap.addStretch()
        lay.addLayout(wrap)
        lay.addSpacing(18)

        title = QLabel("Siparişiniz Alındı!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 22px; font-weight: 800; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(title)

        sub = QLabel("Siparişiniz başarıyla oluşturuldu.\nDetayları aşağıda görebilirsiniz.")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; "
            f"border: none; background: transparent;"
        )
        lay.addWidget(sub)
        lay.addSpacing(20)

        # Bilgi kartı
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_RAISED};
                border: 1px solid {Colors.GOLD}33;
                border-radius: {Radius.MD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(22, 18, 22, 18)
        c_lay.setSpacing(12)

        c_lay.addLayout(self._info_row("Sipariş No",
                                        self._order.order_number or "—",
                                        gold=True))
        c_lay.addLayout(self._info_row("Sipariş Tarihi",
                                        self._order.created_at or "—"))
        c_lay.addLayout(self._info_row("Ödeme Yöntemi",
                                        self._order.payment_method_label()))
        c_lay.addLayout(self._info_row("Toplam Tutar",
                                        f"₺ {self._order.total_amount:,.2f}",
                                        gold=True, big=True))
        lay.addWidget(card)

        lay.addStretch()

        # Butonlar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_close = QPushButton("Kapat")
        btn_close.setFixedHeight(42)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}; font-size: 13px;
                padding: 0 22px;
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD}; color: {Colors.GOLD}; }}
        """)
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)

        btn_orders = QPushButton("📋  Siparişlerime Git")
        btn_orders.setFixedHeight(42)
        btn_orders.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_orders.setStyleSheet(gold_btn())
        btn_orders.clicked.connect(self._on_view_orders)
        btn_row.addWidget(btn_orders, 1)

        lay.addLayout(btn_row)

    def _info_row(self, label: str, value: str,
                   gold: bool = False, big: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        l = QLabel(label)
        l.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 0.5px;"
        )
        v = QLabel(value)
        size = 16 if big else 13
        color = Colors.GOLD_BRIGHT if gold else Colors.TEXT_H1
        weight = 800 if (gold or big) else 600
        v.setStyleSheet(
            f"color: {color}; font-size: {size}px; font-weight: {weight}; "
            f"font-family: {Fonts.FAMILY};"
        )
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(l)
        row.addStretch()
        row.addWidget(v)
        return row

    def _on_view_orders(self) -> None:
        self.view_orders_clicked.emit()
        self.accept()
