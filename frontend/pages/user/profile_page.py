from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Radius, gold_button_style, input_style


class ProfilePage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Profil kartı
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: {Colors.BG_CARD}; border: 1px solid {Colors.BORDER};
                border-radius: {Radius.LG}; }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 24, 28, 24)
        card_lay.setSpacing(16)

        hdr = QLabel("👤  Profil Bilgilerim")
        hdr.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold; border: none;")
        card_lay.addWidget(hdr)

        grid = QHBoxLayout()
        grid.setSpacing(20)
        for label, attr in [("Ad", "_lbl_fn"), ("Soyad", "_lbl_ln"), ("Kullanıcı Adı", "_lbl_un"), ("E-posta", "_lbl_em")]:
            col = QVBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;")
            val = QLabel("—")
            val.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px; border: none;")
            setattr(self, attr, val)
            col.addWidget(l)
            col.addWidget(val)
            grid.addLayout(col)
        card_lay.addLayout(grid)

        # Şifre değiştir
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {Colors.BORDER}; border: none; border-top: 1px solid {Colors.BORDER};")
        card_lay.addWidget(sep)

        pass_title = QLabel("🔒  Şifre Değiştir")
        pass_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px; font-weight: bold; border: none;")
        card_lay.addWidget(pass_title)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(12)
        self._old_pass = QLineEdit()
        self._old_pass.setPlaceholderText("Mevcut şifre")
        self._old_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._old_pass.setFixedHeight(38)
        self._old_pass.setStyleSheet(input_style())
        self._new_pass = QLineEdit()
        self._new_pass.setPlaceholderText("Yeni şifre")
        self._new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pass.setFixedHeight(38)
        self._new_pass.setStyleSheet(input_style())
        btn_change = QPushButton("Değiştir")
        btn_change.setFixedHeight(38)
        btn_change.setStyleSheet(gold_button_style())
        btn_change.clicked.connect(self._change_password)
        pass_row.addWidget(self._old_pass)
        pass_row.addWidget(self._new_pass)
        pass_row.addWidget(btn_change)
        card_lay.addLayout(pass_row)

        self._pass_msg = QLabel("")
        self._pass_msg.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 12px; border: none;")
        card_lay.addWidget(self._pass_msg)
        root.addWidget(card)

        # Sipariş geçmişi
        ord_title = QLabel("📋  Sipariş Geçmişim")
        ord_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        root.addWidget(ord_title)

        self._ord_table = QTableWidget(0, 4)
        self._ord_table.setHorizontalHeaderLabels(["Sipariş #", "Tutar (₺)", "Durum", "Tarih"])
        self._ord_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._ord_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._ord_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ord_table.verticalHeader().setVisible(False)
        self._ord_table.setStyleSheet(f"""
            QTableWidget {{ background: {Colors.BG_CARD}; border: none;
                gridline-color: {Colors.BORDER}; border-radius: {Radius.LG}; }}
            QHeaderView::section {{ background: {Colors.BG_ELEVATED}; color: {Colors.GOLD_PRIMARY};
                border: none; padding: 8px; font-weight: bold; }}
        """)
        root.addWidget(self._ord_table)

    def refresh(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        self._lbl_fn.setText(user.first_name)
        self._lbl_ln.setText(user.last_name)
        self._lbl_un.setText(user.username)
        self._lbl_em.setText(user.email)

        orders = self._ctx.order_service.get_user_orders(user.id)
        status_colors = {
            "pending": Colors.WARNING, "processing": Colors.INFO,
            "completed": Colors.SUCCESS, "cancelled": Colors.ERROR,
        }
        self._ord_table.setRowCount(len(orders))
        for r, o in enumerate(orders):
            self._ord_table.setItem(r, 0, QTableWidgetItem(f"#{o.id}"))
            self._ord_table.setItem(r, 1, QTableWidgetItem(f"₺ {o.total_amount:,.2f}"))
            s_item = QTableWidgetItem(o.status_label())
            s_item.setForeground(QColor(status_colors.get(o.status, Colors.TEXT_MUTED)))
            self._ord_table.setItem(r, 2, s_item)
            self._ord_table.setItem(r, 3, QTableWidgetItem(o.created_at[:16]))

    def _change_password(self) -> None:
        from backend.utils.validators import ValidationError
        user = self._ctx.auth_service.get_current_user()
        old  = self._old_pass.text()
        new  = self._new_pass.text()
        try:
            ok = self._ctx.auth_service.change_password(user.id, old, new)
            if ok:
                self._pass_msg.setStyleSheet(f"color: {Colors.SUCCESS}; font-size: 12px; border: none;")
                self._pass_msg.setText("✅  Şifre başarıyla değiştirildi.")
                self._old_pass.clear()
                self._new_pass.clear()
            else:
                self._pass_msg.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px; border: none;")
                self._pass_msg.setText("❌  Mevcut şifre hatalı.")
        except ValidationError as e:
            self._pass_msg.setStyleSheet(f"color: {Colors.ERROR}; font-size: 12px; border: none;")
            self._pass_msg.setText(str(e))
