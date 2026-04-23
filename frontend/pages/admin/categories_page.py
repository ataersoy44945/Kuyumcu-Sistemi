from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from backend.app_context import AppContext
from frontend.styles.app_theme import (
    Colors, Radius, gold_btn, input_field, premium_table
)
from frontend.dialogs.confirm_dialog import ConfirmDialog
from frontend.utils import category_icon


class CategoriesPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 20)
        lay.setSpacing(16)

        top = QHBoxLayout()
        top.addStretch()
        btn_add = QPushButton("  +  Yeni Kategori")
        btn_add.setFixedHeight(40)
        btn_add.setStyleSheet(gold_btn())
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_cat)
        top.addWidget(btn_add)
        lay.addLayout(top)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["#", "Kategori", "Açıklama", "Ürün", "İşlemler"]
        )
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 48)
        self._table.setColumnWidth(3, 100)
        self._table.setColumnWidth(4, 170)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(premium_table() + f"""
            QTableWidget {{ background: {Colors.BG_SURFACE}; border-radius: {Radius.LG}; }}
            QTableWidget::item:alternate {{ background: rgba(25,36,64,0.4); }}
        """)
        lay.addWidget(self._table)

    def refresh(self) -> None:
        rows = self._ctx.product_service.get_categories_with_counts(active_only=False)
        self._table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            c     = row["category"]
            count = row["product_count"]

            self._table.setRowHeight(r, 56)
            self._table.setItem(r, 0, self._cell(str(c.id), Qt.AlignmentFlag.AlignCenter))

            # Kategori adı — ikon + metin
            name_item = QTableWidgetItem(f"  {category_icon(c.name)}   {c.name}")
            name_item.setForeground(QColor(Colors.TEXT_H1))
            self._table.setItem(r, 1, name_item)

            self._table.setItem(r, 2, self._cell(c.description or "—"))

            # Ürün sayısı — sade renkli metin
            cnt_item = QTableWidgetItem(f"{count} ürün" if count else "—")
            cnt_item.setForeground(
                QColor(Colors.GOLD if count > 0 else Colors.TEXT_MUTED)
            )
            cnt_item.setTextAlignment(
                int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            )
            self._table.setItem(r, 3, cnt_item)

            # İşlem butonları — sadece ikon (tooltip'li)
            self._table.setCellWidget(r, 4, self._build_action_buttons(c))

    # ── İşlem butonları ──────────────────────────────────────

    def _build_action_buttons(self, cat) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 8, 6, 8)
        lay.setSpacing(6)

        btn_edit = QPushButton("Düzenle")
        btn_edit.setFixedSize(86, 36)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet(self._text_btn_style("#3B82F6", "#1E3A8A"))
        btn_edit.clicked.connect(lambda _, c=cat: self._edit_cat(c))

        btn_del = QPushButton("Sil")
        btn_del.setFixedSize(64, 36)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setStyleSheet(self._text_btn_style("#EF4444", "#7F1D1D"))
        btn_del.clicked.connect(lambda _, c=cat: self._delete_cat(c))

        lay.addWidget(btn_edit)
        lay.addWidget(btn_del)
        lay.addStretch()
        return w

    @staticmethod
    def _text_btn_style(color: str, deep: str) -> str:
        """Solid arka planlı belirgin buton."""
        return f"""
            QPushButton {{
                background: {deep};
                color: #FFFFFF;
                border: 1px solid {color};
                border-radius: 6px;
                font-size: 12px; font-weight: 600;
                padding: 0 8px;
            }}
            QPushButton:hover {{
                background: {color};
                border-color: {color};
            }}
            QPushButton:pressed {{
                background: {deep};
            }}
        """

    # ── Aksiyonlar ───────────────────────────────────────────

    def _add_cat(self) -> None:
        name, ok = self._prompt("Yeni Kategori", "Kategori adı:")
        if ok and name:
            try:
                self._ctx.product_service.add_category(name)
                self.refresh()
            except ValueError:
                pass

    def _edit_cat(self, cat) -> None:
        name, ok = self._prompt("Kategori Düzenle", "Kategori adı:", default=cat.name)
        if ok and name:
            self._ctx.product_service.update_category(cat.id, name)
            self.refresh()

    def _delete_cat(self, cat) -> None:
        if ConfirmDialog.ask(self, "Kategori Sil", f'"{cat.name}" silinsin mi?'):
            self._ctx.product_service.delete_category(cat.id)
            self.refresh()

    def _prompt(self, title: str, label: str, default: str = "") -> tuple[str, bool]:
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(380, 170)
        dlg.setStyleSheet(f"QDialog {{ background: {Colors.BG_SURFACE}; }}")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.setSpacing(10)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {Colors.TEXT_BODY}; font-size: 13px;")
        lay.addWidget(lbl)
        inp = QLineEdit(default)
        inp.setFixedHeight(40)
        inp.setStyleSheet(input_field())
        lay.addWidget(inp)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        ok = dlg.exec() == QDialog.DialogCode.Accepted
        return inp.text().strip(), ok

    @staticmethod
    def _cell(text: str,
              align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
              ) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(int(align))
        return item
