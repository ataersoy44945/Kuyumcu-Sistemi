"""
Premium Koyu Tema — Kuyumcu Pro Dashboard
Tüm renk, font ve QSS tanımları tek merkezden yönetilir.
"""


class Colors:
    # ── Ana Arka Planlar (Lacivert/Antrasit) ──────────────────
    BG_BASE      = "#080D18"   # En koyu — pencere zemini
    BG_SURFACE   = "#0D1628"   # Kart yüzeyleri
    BG_RAISED    = "#111C30"   # Sidebar, header
    BG_ELEVATED  = "#182338"   # Hover, yükseltilmiş kartlar
    BG_INPUT     = "#0F1A2E"   # Form alanları

    # ── Backward-compat alias'lar ─────────────────────────────
    BG_DARK      = "#080D18"
    BG_CARD      = "#0D1628"

    # ── Kenarlıklar ───────────────────────────────────────────
    BORDER_DIM     = "#182338"
    BORDER_DEFAULT = "#1E3050"
    BORDER_BRIGHT  = "#2A4070"
    BORDER         = "#1E3050"   # alias

    # ── Altın Paleti ──────────────────────────────────────────
    GOLD         = "#D4AF37"
    GOLD_BRIGHT  = "#F0C93A"
    GOLD_LIGHT   = "#FFD700"
    GOLD_DIM     = "#9C7E22"
    GOLD_SUBTLE  = "rgba(212,175,55,0.10)"
    GOLD_SUBTLE2 = "rgba(212,175,55,0.05)"
    GOLD_PRIMARY = "#D4AF37"   # alias

    # ── Metin ─────────────────────────────────────────────────
    TEXT_H1        = "#EEF2FF"
    TEXT_BODY      = "#A8B8D8"
    TEXT_MUTED     = "#4A5E80"
    TEXT_ON_GOLD   = "#080D18"
    TEXT_PRIMARY   = "#EEF2FF"   # alias
    TEXT_SECONDARY = "#A8B8D8"   # alias

    # ── Durum Renkleri ────────────────────────────────────────
    GREEN    = "#22C55E";  GREEN_BG  = "rgba(34,197,94,0.10)"
    AMBER    = "#F59E0B";  AMBER_BG  = "rgba(245,158,11,0.10)"
    RED      = "#EF4444";  RED_BG    = "rgba(239,68,68,0.10)"
    BLUE     = "#3B82F6";  BLUE_BG   = "rgba(59,130,246,0.10)"

    # ── Durum alias'lar ───────────────────────────────────────
    SUCCESS  = "#22C55E"
    WARNING  = "#F59E0B"
    ERROR    = "#EF4444"
    INFO     = "#3B82F6"

    # ── Kripto ────────────────────────────────────────────────
    BTC    = "#F7931A"
    BTC_BG = "rgba(247,147,26,0.10)"


class Fonts:
    FAMILY         = "Segoe UI"
    FAMILY_PRIMARY = "Segoe UI"   # alias
    FAMILY_M       = "Consolas"
    SZ_XS  = 10;  SZ_SM  = 12;  SZ_BASE = 13
    SZ_MD  = 15;  SZ_LG  = 18;  SZ_XL   = 22
    SZ_2XL = 28;  SZ_3XL = 36


class Radius:
    SM   = "6px"
    MD   = "10px"
    LG   = "14px"
    XL   = "20px"
    FULL = "999px"


# ── QSS Bileşenleri ───────────────────────────────────────────

def global_style() -> str:
    return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {Colors.BG_BASE};
            color: {Colors.TEXT_BODY};
            font-family: {Fonts.FAMILY};
            font-size: {Fonts.SZ_BASE}px;
        }}
        QScrollBar:vertical {{
            background: {Colors.BG_SURFACE};
            width: 5px; border-radius: 3px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.BORDER_BRIGHT}; border-radius: 3px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {Colors.GOLD_DIM}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: {Colors.BG_SURFACE}; height: 5px; border-radius: 3px;
        }}
        QScrollBar::handle:horizontal {{
            background: {Colors.BORDER_BRIGHT}; border-radius: 3px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QToolTip {{
            background: {Colors.BG_ELEVATED}; color: {Colors.TEXT_H1};
            border: 1px solid {Colors.BORDER_DEFAULT}; border-radius: {Radius.SM};
            padding: 5px 10px; font-size: {Fonts.SZ_SM}px;
        }}
        QMessageBox {{ background: {Colors.BG_SURFACE}; }}
    """


def gold_btn() -> str:
    return f"""
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});
            color: {Colors.TEXT_ON_GOLD};
            border: none; border-radius: {Radius.MD};
            padding: 0 22px; height: 36px;
            font-size: {Fonts.SZ_BASE}px; font-weight: 700;
            font-family: {Fonts.FAMILY};
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #FFD700, stop:1 {Colors.GOLD_BRIGHT});
        }}
        QPushButton:pressed {{ background: {Colors.GOLD_DIM}; }}
        QPushButton:disabled {{
            background: {Colors.BORDER_DEFAULT}; color: {Colors.TEXT_MUTED};
        }}
    """


def ghost_btn() -> str:
    return f"""
        QPushButton {{
            background: transparent; color: {Colors.GOLD};
            border: 1px solid {Colors.GOLD}; border-radius: {Radius.MD};
            padding: 0 20px; height: 36px;
            font-size: {Fonts.SZ_BASE}px; font-family: {Fonts.FAMILY};
        }}
        QPushButton:hover {{
            background: {Colors.GOLD_SUBTLE}; color: {Colors.GOLD_BRIGHT};
        }}
        QPushButton:pressed {{ background: {Colors.GOLD_SUBTLE2}; }}
    """


def danger_btn() -> str:
    return f"""
        QPushButton {{
            background: transparent; color: {Colors.RED};
            border: 1px solid {Colors.RED}44; border-radius: {Radius.MD};
            padding: 0 18px; height: 34px; font-size: {Fonts.SZ_SM}px;
        }}
        QPushButton:hover {{
            background: {Colors.RED_BG}; border-color: {Colors.RED};
        }}
    """


def input_field() -> str:
    return f"""
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {Colors.BG_INPUT}; color: {Colors.TEXT_H1};
            border: 1px solid {Colors.BORDER_DEFAULT}; border-radius: {Radius.SM};
            padding: 6px 12px; font-size: {Fonts.SZ_BASE}px;
            font-family: {Fonts.FAMILY};
            selection-background-color: {Colors.GOLD_SUBTLE};
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
        QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {Colors.GOLD}; background: {Colors.BG_ELEVATED};
        }}
        QLineEdit::placeholder {{ color: {Colors.TEXT_MUTED}; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
        QComboBox QAbstractItemView {{
            background: {Colors.BG_ELEVATED}; color: {Colors.TEXT_BODY};
            border: 1px solid {Colors.BORDER_DEFAULT};
            selection-background-color: {Colors.GOLD_SUBTLE};
            selection-color: {Colors.GOLD}; outline: none;
        }}
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background: {Colors.BG_ELEVATED}; border: none; width: 18px;
        }}
    """


def premium_table() -> str:
    return f"""
        QTableWidget {{
            background: {Colors.BG_SURFACE}; color: {Colors.TEXT_BODY};
            border: none; gridline-color: {Colors.BORDER_DIM};
            border-radius: {Radius.LG}; outline: none;
        }}
        QTableWidget::item {{
            padding: 11px 14px; border-bottom: 1px solid {Colors.BORDER_DIM};
        }}
        QTableWidget::item:hover {{
            background: {Colors.BG_ELEVATED}; color: {Colors.TEXT_H1};
        }}
        QTableWidget::item:selected {{
            background: {Colors.GOLD_SUBTLE}; color: {Colors.GOLD};
        }}
        QHeaderView::section {{
            background: {Colors.BG_RAISED}; color: {Colors.TEXT_MUTED};
            border: none; border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            padding: 11px 14px; font-size: {Fonts.SZ_SM}px;
            font-weight: 700; letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        QHeaderView {{ background: {Colors.BG_RAISED}; }}
        QTableWidget::item:alternate {{ background: {Colors.BG_RAISED}; }}
    """


def page_card(border_color: str = None) -> str:
    bc = border_color or Colors.BORDER_DEFAULT
    return f"""
        QFrame {{
            background: {Colors.BG_SURFACE};
            border: 1px solid {bc};
            border-radius: {Radius.LG};
        }}
    """


# ── Alias'lar (geriye dönük uyumluluk) ───────────────────────
gold_button_style  = gold_btn
ghost_button_style = ghost_btn
input_style        = input_field
