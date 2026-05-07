"""
SavedCardsDialog — kullanıcının kayıtlı kartlarını yönetmesi için modal.

Listeler, varsayılan yapar, siler. Yeni kart ekleme akışı checkout
sayfasında yaşar.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea,
    QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.app_context import AppContext
from backend.models.saved_card import SavedCard
from frontend.styles.app_theme import Colors, Fonts, Radius
from frontend.dialogs.confirm_dialog import ConfirmDialog
from frontend.components.toast import Toast


class SavedCardsDialog(QDialog):

    cards_changed = pyqtSignal()   # Liste güncellendiğinde

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self._ctx = ctx
        self._build_ui()
        self.refresh()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle("Kayıtlı Kartlarım")
        self.setModal(True)
        self.setFixedSize(560, 540)
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        head = QLabel("💳  Kayıtlı Kartlarım")
        head.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700;"
        )
        lay.addWidget(head)

        sub = QLabel(
            "Kart numarası ve CVV güvenlik gereği saklanmaz — "
            "ödeme sırasında her seferinde tekrar sorulur."
        )
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px;")
        lay.addWidget(sub)
        lay.addSpacing(4)

        # Kart listesi (scroll)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        self._list_w = QWidget()
        self._list_w.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(10)
        self._list_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._list_w)
        lay.addWidget(self._scroll, 1)

        # Boş durum
        self._empty_lbl = QLabel(
            "💳\nHenüz kayıtlı kartınız yok.\n"
            "Ödeme sayfasında 'Bu kartı kaydet' seçeneğini işaretleyerek ekleyebilirsiniz."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 13px; padding: 60px 20px;"
        )
        self._empty_lbl.hide()
        lay.addWidget(self._empty_lbl)

        # Kapat butonu
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Kapat")
        btn_close.setFixedSize(110, 38)
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
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

    # ── Veri ─────────────────────────────────────────────────

    def refresh(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return

        # Önceki kart kartlarını temizle
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cards = self._ctx.saved_card_service.list_for_user(user.id)
        if not cards:
            self._empty_lbl.show()
            self._scroll.hide()
            return

        self._empty_lbl.hide()
        self._scroll.show()
        for c in cards:
            self._list_lay.addWidget(self._build_card_row(c))

    # ── Kart satırı ──────────────────────────────────────────

    def _build_card_row(self, card: SavedCard) -> QFrame:
        frame = QFrame()
        border = Colors.GOLD if card.is_default else Colors.BORDER_DEFAULT
        frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_RAISED};
                border: 1px solid {border}66;
                border-radius: {Radius.MD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(14)

        # Marka ikonu
        brand = QLabel(card.brand_icon())
        brand.setFixedSize(46, 46)
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {Colors.GOLD_DIM}, stop:1 {Colors.GOLD_BRIGHT});
            color: {Colors.TEXT_ON_GOLD};
            font-size: 22px; font-weight: 800;
            border-radius: {Radius.SM};
        """)
        lay.addWidget(brand)

        # Bilgi sütunu
        col = QVBoxLayout()
        col.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title = QLabel(card.display_title())
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700;"
        )
        title_row.addWidget(title)
        if card.is_default:
            badge = QLabel("VARSAYILAN")
            badge.setStyleSheet(
                f"color: {Colors.GOLD}; background: {Colors.GOLD_SUBTLE}; "
                f"font-size: 9px; font-weight: 800; padding: 2px 8px; "
                f"border: 1px solid {Colors.GOLD}55; border-radius: {Radius.FULL};"
            )
            title_row.addWidget(badge)
        title_row.addStretch()
        col.addLayout(title_row)

        masked = QLabel(card.masked_number())
        masked.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 13px; "
            f"font-family: {Fonts.FAMILY_M}; letter-spacing: 1.5px;"
        )
        col.addWidget(masked)

        meta = QLabel(f"{card.holder}  ·  Son Kul. {card.expiry_text()}")
        meta.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 10px;")
        col.addWidget(meta)
        lay.addLayout(col, 1)

        # Aksiyon butonları
        actions = QVBoxLayout()
        actions.setSpacing(6)
        actions.setAlignment(Qt.AlignmentFlag.AlignRight)

        if not card.is_default:
            btn_def = QPushButton("Varsayılan Yap")
            btn_def.setFixedHeight(28)
            btn_def.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_def.setStyleSheet(self._mini_btn_style(Colors.GOLD))
            btn_def.clicked.connect(lambda _=False, c=card: self._set_default(c))
            actions.addWidget(btn_def)

        btn_del = QPushButton("Sil")
        btn_del.setFixedHeight(28)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(self._mini_btn_style(Colors.RED))
        btn_del.clicked.connect(lambda _=False, c=card: self._delete(c))
        actions.addWidget(btn_del)

        lay.addLayout(actions)
        return frame

    @staticmethod
    def _mini_btn_style(color: str) -> str:
        return f"""
            QPushButton {{
                background: transparent; color: {color};
                border: 1px solid {color}66; border-radius: {Radius.SM};
                font-size: 11px; font-weight: 600; padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {color}22; border-color: {color};
            }}
        """

    # ── Aksiyonlar ───────────────────────────────────────────

    def _set_default(self, card: SavedCard) -> None:
        user = self._ctx.auth_service.get_current_user()
        if self._ctx.saved_card_service.set_default(user.id, card.id):
            Toast.show_success(self, "Varsayılan kart güncellendi")
            self.cards_changed.emit()
            self.refresh()

    def _delete(self, card: SavedCard) -> None:
        if not ConfirmDialog.ask(
            self, "Kartı Sil",
            f"{card.display_title()} silinecek. Onaylıyor musunuz?"
        ):
            return
        user = self._ctx.auth_service.get_current_user()
        if self._ctx.saved_card_service.delete(user.id, card.id):
            Toast.show_info(self, "Kart silindi")
            self.cards_changed.emit()
            self.refresh()
