from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from frontend.styles.app_theme import Colors, Fonts, Radius


class RateCard(QFrame):
    """Tek bir döviz/altın kurunu gösteren küçük kart bileşeni."""

    def __init__(self, icon: str, label: str, value: str = "—",
                 change: str = "", color: str = None, parent=None):
        super().__init__(parent)
        color = color or Colors.GOLD
        self.setFixedSize(168, 92)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-top: 2px solid {color};
                border-radius: {Radius.MD};
            }}
            QFrame:hover {{
                background: {Colors.BG_ELEVATED};
            }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(3)

        header = QLabel(f"{icon}  {label}")
        header.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            f"background: transparent; border: none; letter-spacing: 0.3px;"
        )

        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(
            f"color: {color}; font-size: 16px; font-weight: 700; "
            f"background: transparent; border: none; font-family: {Fonts.FAMILY_M};"
        )

        self._change_lbl = QLabel(change)
        self._change_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; "
            f"background: transparent; border: none;"
        )

        lay.addWidget(header)
        lay.addWidget(self._value_lbl)
        lay.addWidget(self._change_lbl)

    def update_value(self, value: str, change: str = "") -> None:
        self._value_lbl.setText(value)
        self._change_lbl.setText(change)
