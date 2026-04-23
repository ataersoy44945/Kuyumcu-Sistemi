from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Radius, input_field, premium_table
from frontend.dialogs.confirm_dialog import ConfirmDialog


class OrdersPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(16)

        # ── Filtre çubuğu ─────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)

        lbl = QLabel("Durum:")
        lbl.setStyleSheet(f"color: {Colors.TEXT_BODY}; font-size: 13px;")
        self._status_filter = QComboBox()
        self._status_filter.setFixedHeight(40)
        self._status_filter.setFixedWidth(190)
        self._status_filter.setStyleSheet(input_field())
        self._status_filter.addItem("Tüm Siparişler", None)
        for k, v in {
            "pending":    "⏳  Beklemede",
            "processing": "⚙️  İşlemde",
            "completed":  "✅  Tamamlandı",
            "cancelled":  "❌  İptal",
        }.items():
            self._status_filter.addItem(v, k)
        self._status_filter.currentIndexChanged.connect(self.refresh)

        top.addWidget(lbl)
        top.addWidget(self._status_filter)
        top.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        top.addWidget(self._count_lbl)
        lay.addLayout(top)

        # ── Tablo ─────────────────────────────────────────────
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Müşteri", "Ürün Adedi", "Toplam", "Durum", "Tarih", "İşlemler"]
        )
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(6, 160)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(premium_table() + f"""
            QTableWidget {{ background: {Colors.BG_SURFACE}; border-radius: {Radius.LG}; }}
            QTableWidget::item:alternate {{ background: rgba(25,36,64,0.4); }}
        """)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        status = self._status_filter.currentData()
        orders = (
            self._ctx.order_service.get_all_orders() if status is None
            else self._ctx.order_repo.get_by_status(status)
        )
        status_colors = {
            "pending":    Colors.AMBER,
            "processing": Colors.BLUE,
            "completed":  Colors.GREEN,
            "cancelled":  Colors.RED,
        }
        self._table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            self._table.setRowHeight(r, 48)
            self._table.setItem(r, 0, self._cell(f"#{o.id}", Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(r, 1, self._cell(o.user_full_name or f"#{o.user_id}"))
            self._table.setItem(r, 2, self._cell(
                str(len(o.items)), Qt.AlignmentFlag.AlignCenter
            ))
            self._table.setItem(r, 3, self._cell(f"₺ {o.total_amount:,.2f}"))

            s_item = QTableWidgetItem(o.status_label())
            s_item.setForeground(QColor(status_colors.get(o.status, Colors.TEXT_MUTED)))
            self._table.setItem(r, 4, s_item)
            self._table.setItem(r, 5, self._cell(o.created_at[:16]))

            # İşlem butonları — sipariş durumuna göre
            self._table.setCellWidget(r, 6, self._build_action_buttons(o))

        self._count_lbl.setText(f"{len(orders)} sipariş")

    # ── İşlem butonları ──────────────────────────────────────

    def _build_action_buttons(self, order) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(6)

        if order.status == "pending":
            # ✓ Onayla  (pending → processing)
            btn_approve = self._action_btn(
                "✓", "Siparişi onayla (İşleme al)", Colors.GREEN
            )
            btn_approve.clicked.connect(
                lambda _, oid=order.id: self._approve(oid)
            )
            lay.addWidget(btn_approve)

            # ✕ Reddet  (pending → cancelled)
            btn_reject = self._action_btn(
                "✕", "Siparişi reddet / iptal et", Colors.RED
            )
            btn_reject.clicked.connect(
                lambda _, oid=order.id: self._reject(oid)
            )
            lay.addWidget(btn_reject)

        elif order.status == "processing":
            # ✓ Tamamla
            btn_complete = self._action_btn(
                "✓", "Siparişi tamamla", Colors.GREEN
            )
            btn_complete.clicked.connect(
                lambda _, oid=order.id: self._complete(oid)
            )
            lay.addWidget(btn_complete)

            # ✕ İptal
            btn_cancel = self._action_btn(
                "✕", "Siparişi iptal et", Colors.RED
            )
            btn_cancel.clicked.connect(
                lambda _, oid=order.id: self._reject(oid)
            )
            lay.addWidget(btn_cancel)

        else:
            # Tamamlanmış / iptal edilmiş — sadece durum etiketi
            done = QLabel("—")
            done.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 14px;"
            )
            done.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(done)

        lay.addStretch()
        return w

    @staticmethod
    def _action_btn(icon: str, tooltip: str, color: str) -> QPushButton:
        btn = QPushButton(icon)
        btn.setFixedSize(32, 30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {color};
                border: 1px solid {color}55; border-radius: 6px;
                font-size: 13px; font-weight: 800;
            }}
            QPushButton:hover {{
                background: {color}22; border-color: {color};
            }}
        """)
        return btn

    # ── Aksiyonlar ────────────────────────────────────────────

    def _approve(self, order_id: int) -> None:
        if not ConfirmDialog.ask(
            self, "Siparişi Onayla",
            f"#{order_id} numaralı sipariş 'İşlemde' durumuna alınacak. Onaylıyor musunuz?",
        ):
            return
        try:
            self._ctx.order_service.update_status(order_id, "processing")
        except Exception:
            pass
        self.refresh()

    def _reject(self, order_id: int) -> None:
        if not ConfirmDialog.ask(
            self, "Siparişi İptal Et",
            f"#{order_id} numaralı sipariş iptal edilecek. Emin misiniz?",
        ):
            return
        try:
            self._ctx.order_service.update_status(order_id, "cancelled")
        except Exception:
            pass
        self.refresh()

    def _complete(self, order_id: int) -> None:
        if not ConfirmDialog.ask(
            self, "Siparişi Tamamla",
            f"#{order_id} numaralı sipariş 'Tamamlandı' olarak işaretlenecek. Onaylıyor musunuz?",
        ):
            return
        try:
            self._ctx.order_service.update_status(order_id, "completed")
        except Exception:
            pass
        self.refresh()

    @staticmethod
    def _cell(text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
              ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(align))
        return item
