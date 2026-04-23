from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QDoubleSpinBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Fonts, Radius, gold_btn, input_field


class _RateCard(QFrame):
    """Tek bir kur değerini gösteren premium bilgi kartı."""

    def __init__(self, icon: str, label: str, color: str = None):
        super().__init__()
        color = color or Colors.GOLD
        self.setMinimumHeight(92)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-top: 3px solid {color};
                border-radius: {Radius.LG};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        header = QLabel(f"{icon}  {label}")
        header.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; font-weight: 600; "
            f"background: transparent; border: none; letter-spacing: 0.3px;"
        )

        self._val = QLabel("—")
        self._val.setStyleSheet(
            f"color: {color}; font-size: 20px; font-weight: 700; "
            f"background: transparent; border: none; font-family: {Fonts.FAMILY_M};"
        )

        lay.addWidget(header)
        lay.addWidget(self._val)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class RatesPage(QWidget):

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setGeometry(0, 0, 9999, 9999)

        inner = QWidget()
        inner.setStyleSheet(f"background: {Colors.BG_BASE};")
        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        lay = QVBoxLayout(inner)
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(20)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Başlık ────────────────────────────────────────────
        header_row = QHBoxLayout()
        title = QLabel("📊  Güncel Piyasa Kurları")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; border: none;"
        )
        self._update_lbl = QLabel("")
        self._update_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self._update_lbl)
        lay.addLayout(header_row)

        # ── Kur kartları grid ─────────────────────────────────
        self._rate_cards: dict[str, _RateCard] = {}
        fields = [
            ("usd_try",          "💵", "Dolar / TL",       Colors.BLUE),
            ("eur_try",          "💶", "Euro / TL",         Colors.GREEN),
            ("gold_gram_try",    "🪙", "Gram Altın / TL",   Colors.GOLD),
            ("gold_quarter_try", "🪙", "Çeyrek Altın / TL", Colors.GOLD),
            ("gold_half_try",    "🪙", "Yarım Altın / TL",  Colors.GOLD),
            ("gold_full_try",    "🪙", "Tam Altın / TL",    Colors.GOLD),
        ]
        grid = QGridLayout()
        grid.setSpacing(14)
        for i, (key, icon, label, color) in enumerate(fields):
            card = _RateCard(icon, label, color)
            self._rate_cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
        lay.addLayout(grid)

        # ── Durum etiketi ─────────────────────────────────────
        self._status_lbl = QLabel("Veriler 60 saniyede bir otomatik güncellenmektedir.")
        self._status_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none; "
            f"padding: 8px 0;"
        )
        lay.addWidget(self._status_lbl)

        # ── Manuel kur girişi ─────────────────────────────────
        man_frame = QFrame()
        man_frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-radius: {Radius.LG};
            }}
        """)
        man_lay = QVBoxLayout(man_frame)
        man_lay.setContentsMargins(24, 20, 24, 20)
        man_lay.setSpacing(14)

        man_title = QLabel("✏️  Manuel Kur Girişi")
        man_title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 15px; font-weight: 700; border: none;"
        )
        man_lay.addWidget(man_title)

        man_sub = QLabel(
            "Otomatik veri alınamadığında veya farklı bir kur kullanmak istediğinizde "
            "aşağıdan manuel giriş yapabilirsiniz."
        )
        man_sub.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 12px; border: none;"
        )
        man_sub.setWordWrap(True)
        man_lay.addWidget(man_sub)

        inp_grid = QGridLayout()
        inp_grid.setSpacing(12)
        spin_defs = [
            ("Dolar / TL",     "_m_usd"),
            ("Euro / TL",      "_m_eur"),
            ("Gram Altın / TL","_m_gold"),
        ]
        for col, (lbl_text, attr) in enumerate(spin_defs):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(
                f"color: {Colors.TEXT_BODY}; font-size: 12px; font-weight: 600; border: none;"
            )
            spin = QDoubleSpinBox()
            spin.setRange(0.01, 9_999_999)
            spin.setDecimals(4)
            spin.setFixedHeight(40)
            spin.setStyleSheet(input_field())
            setattr(self, attr, spin)
            inp_grid.addWidget(lbl,  0, col)
            inp_grid.addWidget(spin, 1, col)
        man_lay.addLayout(inp_grid)

        btn_save = QPushButton("  ✓  Manuel Kuru Kaydet")
        btn_save.setFixedHeight(42)
        btn_save.setFixedWidth(220)
        btn_save.setStyleSheet(gold_btn())
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._save_manual)
        man_lay.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(man_frame)
        lay.addStretch()

    def refresh(self) -> None:
        rates = self._ctx.exchange_service.get_rates()
        if not rates:
            return

        mapping = {
            "usd_try":          (rates.usd_try,          "₺ {:,.4f}"),
            "eur_try":          (rates.eur_try,           "₺ {:,.4f}"),
            "gold_gram_try":    (rates.gold_gram_try,     "₺ {:,.2f}"),
            "gold_quarter_try": (rates.gold_quarter_try,  "₺ {:,.2f}"),
            "gold_half_try":    (rates.gold_half_try,     "₺ {:,.2f}"),
            "gold_full_try":    (rates.gold_full_try,     "₺ {:,.2f}"),
        }
        for key, (val, fmt) in mapping.items():
            self._rate_cards[key].set_value(fmt.format(val) if val else "—")

        ts = self._ctx.exchange_service.last_update_label()
        self._update_lbl.setText(ts)

        self._m_usd.setValue(rates.usd_try)
        self._m_eur.setValue(rates.eur_try)
        self._m_gold.setValue(rates.gold_gram_try)

    def _save_manual(self) -> None:
        self._ctx.exchange_service.set_manual(
            usd_try=self._m_usd.value(),
            eur_try=self._m_eur.value(),
            gold_gram_try=self._m_gold.value(),
        )
        self.refresh()
