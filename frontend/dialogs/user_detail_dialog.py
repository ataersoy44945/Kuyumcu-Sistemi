"""
UserDetailDialog — admin panelinden kullanıcı detayı.

Sol: kullanıcı profili (avatar, isim, iletişim, rol, durum, engelle butonu)
Sağ: istatistik kartları + sipariş geçmişi tablosu
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from backend.models.user import User
from frontend.styles.app_theme import Colors, Fonts, Radius, premium_table


# ════════════════════════════════════════════════════════════
#  STAT KARTI
# ════════════════════════════════════════════════════════════

class _StatBox(QFrame):
    """Detay paneli için küçük istatistik kartı."""

    def __init__(self, label: str, value: str, color: str, icon: str = ""):
        super().__init__()
        self.setFixedHeight(82)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-top: 2px solid {color};
                border-radius: {Radius.MD};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(3)

        hdr = QLabel(f"{icon}  {label}".strip())
        hdr.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.8px; border: none; background: transparent;"
        )
        val = QLabel(value)
        val.setStyleSheet(
            f"color: {color}; font-size: 19px; font-weight: 700; "
            f"font-family: {Fonts.FAMILY}; border: none; background: transparent;"
        )
        lay.addWidget(hdr)
        lay.addWidget(val)


# ════════════════════════════════════════════════════════════
#  KULLANICI DETAY DIALOGU
# ════════════════════════════════════════════════════════════

class UserDetailDialog(QDialog):

    user_changed = pyqtSignal(int)    # kullanıcı güncellenince yayınlanır

    _STATUS_COLORS = {
        "pending":    Colors.AMBER,
        "processing": Colors.BLUE,
        "completed":  Colors.GREEN,
        "cancelled":  Colors.RED,
    }

    def __init__(self, ctx: AppContext, user: User, parent=None):
        super().__init__(parent)
        self._ctx  = ctx
        self._user = user
        self._stats: dict = {}

        self.setWindowTitle(f"Kullanıcı — {user.full_name()}")
        self.setModal(True)
        self.setFixedSize(960, 640)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_BASE};
                border: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)

        self._build_ui()
        self._load_data()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_profile_pane(), 0)
        root.addWidget(self._build_stats_pane(), 1)

    # 1) SOL PANEL — kullanıcı profili
    def _build_profile_pane(self) -> QWidget:
        pane = QFrame()
        pane.setFixedWidth(300)
        pane.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {Colors.BG_RAISED}, stop:1 {Colors.BG_SURFACE});
                border-right: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(28, 28, 28, 24)
        lay.setSpacing(14)

        # Avatar
        parts = self._user.full_name().split()
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
        avatar = QLabel(initials)
        avatar.setFixedSize(96, 96)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD_DIM});
            color: {Colors.TEXT_ON_GOLD};
            border-radius: 48px;
            font-size: 34px; font-weight: 800;
            border: none;
        """)
        lay.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)

        # İsim
        name = QLabel(self._user.full_name())
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(name)

        # Rol rozeti
        role_color = Colors.GOLD if self._user.is_admin() else Colors.BLUE
        role = QLabel(self._user.display_role().upper())
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role.setFixedHeight(26)
        role.setStyleSheet(f"""
            color: {role_color};
            background: {role_color}22;
            border: 1px solid {role_color}66;
            border-radius: 13px;
            padding: 0 14px;
            font-size: 10px; font-weight: 700; letter-spacing: 1px;
        """)
        lay.addWidget(role, alignment=Qt.AlignmentFlag.AlignCenter)

        lay.addSpacing(6)

        # İletişim bilgileri
        lay.addWidget(self._info_row("Kullanıcı Adı", self._user.username))
        lay.addWidget(self._info_row("E-posta",        self._user.email))
        lay.addWidget(self._info_row("Telefon",        self._user.phone or "—"))
        lay.addWidget(self._info_row("Kayıt",          (self._user.created_at or "—")[:16]))
        last = self._user.last_login_at or "Henüz giriş yapmamış"
        lay.addWidget(self._info_row("Son Giriş",      last[:16] if last else "—"))

        # Durum
        st_color = Colors.GREEN if self._user.is_active else Colors.RED
        st_txt   = "● Aktif" if self._user.is_active else "○ Engellendi"
        status = QLabel(st_txt)
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setFixedHeight(28)
        status.setStyleSheet(f"""
            color: {st_color};
            background: {st_color}22;
            border: 1px solid {st_color}66;
            border-radius: 14px;
            padding: 0 14px;
            font-size: 11px; font-weight: 700;
        """)
        lay.addSpacing(4)
        lay.addWidget(status, alignment=Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()

        # Engelle / Aktifleştir butonu (adminlere gösterilmez)
        if not self._user.is_admin():
            self._btn_block = QPushButton()
            self._btn_block.setFixedHeight(40)
            self._btn_block.setCursor(Qt.CursorShape.PointingHandCursor)
            self._update_block_button()
            self._btn_block.clicked.connect(self._toggle_block)
            lay.addWidget(self._btn_block)

        # Kapat butonu
        btn_close = QPushButton("Kapat")
        btn_close.setFixedHeight(38)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}; font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD}; color: {Colors.GOLD}; }}
        """)
        btn_close.clicked.connect(self.accept)
        lay.addWidget(btn_close)
        return pane

    def _info_row(self, label: str, value: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(1)
        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.8px; border: none;"
        )
        val = QLabel(value)
        val.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 12px; border: none;"
        )
        val.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addWidget(val)
        return w

    def _update_block_button(self) -> None:
        if self._user.is_active:
            self._btn_block.setText("⛔  Kullanıcıyı Engelle")
            self._btn_block.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {Colors.RED};
                    border: 1px solid {Colors.RED}88;
                    border-radius: {Radius.SM};
                    font-size: 12px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {Colors.RED_BG};
                    border-color: {Colors.RED};
                }}
            """)
        else:
            self._btn_block.setText("✓  Engeli Kaldır")
            self._btn_block.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {Colors.GREEN};
                    border: 1px solid {Colors.GREEN}88;
                    border-radius: {Radius.SM};
                    font-size: 12px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {Colors.GREEN_BG};
                    border-color: {Colors.GREEN};
                }}
            """)

    def _toggle_block(self) -> None:
        new_state = not self._user.is_active
        ok = self._ctx.auth_service.set_user_active(self._user.id, new_state)
        if ok:
            self._user.is_active = new_state
            self.user_changed.emit(self._user.id)
            # Dialogu yenilemek yerine butonu + etiketleri güncelle
            self.accept()

    # 2) SAĞ PANEL — istatistikler + sipariş geçmişi
    def _build_stats_pane(self) -> QWidget:
        pane = QWidget()
        pane.setStyleSheet(f"background: {Colors.BG_BASE};")
        lay = QVBoxLayout(pane)
        lay.setContentsMargins(26, 24, 26, 22)
        lay.setSpacing(14)

        # Başlık
        h = QLabel("📊  Alışveriş Özeti")
        h.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 16px; font-weight: 700; border: none;"
        )
        lay.addWidget(h)

        # İstatistik kartları satırı
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(10)
        lay.addLayout(self._stats_row)

        # Sipariş geçmişi başlığı
        hh = QLabel("🧾  Sipariş Geçmişi")
        hh.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 14px; font-weight: 700; border: none;"
        )
        lay.addSpacing(6)
        lay.addWidget(hh)

        # Sipariş tablosu
        self._orders_table = QTableWidget(0, 5)
        self._orders_table.setHorizontalHeaderLabels(
            ["Sipariş #", "Tarih", "Ürün Adedi", "Tutar", "Durum"]
        )
        hdr = self._orders_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._orders_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._orders_table.verticalHeader().setVisible(False)
        self._orders_table.setShowGrid(False)
        self._orders_table.setAlternatingRowColors(True)
        self._orders_table.setStyleSheet(premium_table() + f"""
            QTableWidget {{ background: {Colors.BG_SURFACE}; border-radius: {Radius.MD}; }}
            QTableWidget::item:alternate {{ background: rgba(25,36,64,0.4); }}
        """)
        lay.addWidget(self._orders_table, 1)

        # Satın alınan ürünler özet etiketi
        self._items_lbl = QLabel("")
        self._items_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        self._items_lbl.setWordWrap(True)
        lay.addWidget(self._items_lbl)
        return pane

    # ── Veri yükleme ──────────────────────────────────────────

    def _load_data(self) -> None:
        self._stats = self._ctx.order_service.get_user_statistics(self._user.id)

        # İstatistik kartlarını doldur (önce temizle)
        while self._stats_row.count():
            w = self._stats_row.takeAt(0).widget()
            if w: w.deleteLater()

        cards = [
            _StatBox("Toplam Sipariş",  str(self._stats["order_count"]),
                     Colors.BLUE,  "📋"),
            _StatBox("Tamamlanan",      str(self._stats["completed_count"]),
                     Colors.GREEN, "✓"),
            _StatBox("Beklemede",       str(self._stats["pending_count"]),
                     Colors.AMBER, "⏳"),
            _StatBox("Toplam Harcama",  f"₺ {self._stats['total_spent']:,.0f}",
                     Colors.GOLD, "💰"),
            _StatBox("Alınan Ürün",     f"{self._stats['item_count']} adet",
                     Colors.GOLD_BRIGHT, "🎁"),
        ]
        for c in cards:
            self._stats_row.addWidget(c, 1)

        # Sipariş tablosu
        orders = self._stats["orders"]
        self._orders_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            self._orders_table.setRowHeight(r, 38)
            self._orders_table.setItem(r, 0, self._cell(f"#{o.id}"))
            self._orders_table.setItem(r, 1, self._cell(o.created_at[:16] if o.created_at else "—"))
            self._orders_table.setItem(r, 2, self._cell(str(len(o.items))))
            self._orders_table.setItem(r, 3, self._cell(f"₺ {o.total_amount:,.2f}"))

            s = QTableWidgetItem(o.status_label())
            s.setForeground(QColor(self._STATUS_COLORS.get(o.status, Colors.TEXT_MUTED)))
            self._orders_table.setItem(r, 4, s)

        # Satın alınan ürünler özeti
        if orders:
            bought: dict[str, int] = {}
            for o in orders:
                if o.status == "cancelled":
                    continue
                for it in o.items:
                    name = it.product_name or f"#{it.product_id}"
                    bought[name] = bought.get(name, 0) + it.quantity
            if bought:
                top = sorted(bought.items(), key=lambda x: -x[1])[:8]
                summary = "Alınan ürünler:  " + "  ·  ".join(
                    f"{n} ({q})" for n, q in top
                )
                self._items_lbl.setText(summary)
            else:
                self._items_lbl.setText("Henüz tamamlanmış alışveriş yok.")
        else:
            self._items_lbl.setText("Bu kullanıcının henüz siparişi yok.")

    @staticmethod
    def _cell(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft))
        return item
