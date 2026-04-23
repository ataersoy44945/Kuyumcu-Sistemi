from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from backend.models.user import User
from frontend.styles.app_theme import (
    Colors, Radius, gold_btn, input_field, premium_table,
)
from frontend.dialogs.user_form_dialog   import UserFormDialog
from frontend.dialogs.user_detail_dialog import UserDetailDialog


class UsersPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._all: list[User] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(16)

        # ── Üst araç çubuğu ───────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Ad, soyad veya kullanıcı adı ile ara…")
        self._search.setFixedHeight(40)
        self._search.setStyleSheet(input_field())
        self._search.textChanged.connect(self._filter)
        top.addWidget(self._search)
        top.addStretch()

        btn_add = QPushButton("  +  Yeni Kullanıcı")
        btn_add.setFixedHeight(40)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet(gold_btn())
        btn_add.clicked.connect(self._add_user)
        top.addWidget(btn_add)
        lay.addLayout(top)

        # ── Tablo ─────────────────────────────────────────────
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels(
            ["#", "Kullanıcı Adı", "Ad Soyad", "E-posta", "Rol", "Durum", "İşlemler"]
        )
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 48)
        self._table.setColumnWidth(6, 220)
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

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px;"
        )
        lay.addWidget(self._count_lbl)

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        self._all = self._ctx.user_repo.get_all()
        self._filter()

    def _filter(self) -> None:
        q = self._search.text().strip().lower()
        filtered = [
            u for u in self._all
            if not q
            or q in u.username.lower()
            or q in u.full_name().lower()
            or q in (u.email or "").lower()
        ]
        self._populate(filtered)

    def _populate(self, users: list[User]) -> None:
        self._table.setRowCount(len(users))
        for r, u in enumerate(users):
            self._table.setRowHeight(r, 56)
            self._table.setItem(r, 0, self._cell(str(u.id), Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(r, 1, self._cell(u.username))
            self._table.setItem(r, 2, self._cell(u.full_name()))
            self._table.setItem(r, 3, self._cell(u.email or "—"))

            role = QTableWidgetItem(u.display_role())
            role.setForeground(QColor(Colors.GOLD if u.is_admin() else Colors.TEXT_BODY))
            self._table.setItem(r, 4, role)

            status = QTableWidgetItem("● Aktif" if u.is_active else "○ Engelli")
            status.setForeground(QColor(Colors.GREEN if u.is_active else Colors.RED))
            self._table.setItem(r, 5, status)

            self._table.setCellWidget(r, 6, self._build_action_buttons(u))

        self._count_lbl.setText(f"{len(users)} kullanıcı")

    # ── İşlem butonları ──────────────────────────────────────

    def _build_action_buttons(self, user: User) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 8, 6, 8)
        lay.setSpacing(6)

        btn_detail = QPushButton("Detay")
        btn_detail.setFixedSize(64, 36)
        btn_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_detail.setStyleSheet(self._btn_style("#D4AF37", "#6B5817"))
        btn_detail.clicked.connect(lambda _, u=user: self._open_detail(u))
        lay.addWidget(btn_detail)

        # Admin hesapları için engelleme gizli (kendi kendini kilitlemesin)
        if not user.is_admin():
            if user.is_active:
                btn_block = QPushButton("Engelle")
                btn_block.setFixedSize(80, 36)
                btn_block.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_block.setStyleSheet(self._btn_style("#EF4444", "#7F1D1D"))
                btn_block.clicked.connect(lambda _, uid=user.id: self._set_active(uid, False))
                lay.addWidget(btn_block)
            else:
                btn_enable = QPushButton("Aktif")
                btn_enable.setFixedSize(60, 36)
                btn_enable.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_enable.setStyleSheet(self._btn_style("#22C55E", "#14532D"))
                btn_enable.clicked.connect(lambda _, uid=user.id: self._set_active(uid, True))
                lay.addWidget(btn_enable)

        lay.addStretch()
        return w

    @staticmethod
    def _btn_style(color: str, deep: str) -> str:
        return f"""
            QPushButton {{
                background: {deep}; color: #FFFFFF;
                border: 1px solid {color}; border-radius: 6px;
                font-size: 12px; font-weight: 600;
                padding: 0 8px;
            }}
            QPushButton:hover {{
                background: {color}; border-color: {color};
            }}
            QPushButton:pressed {{ background: {deep}; }}
        """

    # ── Aksiyonlar ───────────────────────────────────────────

    def _add_user(self) -> None:
        dlg = UserFormDialog(self._ctx, parent=self)
        if dlg.exec() and dlg.created_user:
            self.refresh()

    def _open_detail(self, user: User) -> None:
        dlg = UserDetailDialog(self._ctx, user, parent=self)
        dlg.user_changed.connect(lambda _: self.refresh())
        dlg.exec()
        self.refresh()

    def _set_active(self, user_id: int, active: bool) -> None:
        self._ctx.auth_service.set_user_active(user_id, active)
        self.refresh()

    @staticmethod
    def _cell(text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
              ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(align))
        return item
