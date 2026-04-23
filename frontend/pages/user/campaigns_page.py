"""
Kampanyalar Sayfası — premium kuyumcu markası için lüks indirim paneli.

Yapı:
  ┌──────────────────────────────────────────┐
  │ Başlık şeridi                            │
  │ Özet KPI kartları (aktif / biten / max)  │
  │ Arama + badge filtre çubuğu              │
  │ ◆ Aktif kampanyalar grid                 │
  │ ◯ Süresi dolanlar grid (varsa)           │
  └──────────────────────────────────────────┘

Canlı geri sayım · Hover glow · Badge · Tıklayınca kategoriyi filtrele
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QGraphicsDropShadowEffect,
    QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QCursor

import config
from backend.app_context import AppContext
from backend.models.campaign import Campaign
from frontend.styles.app_theme import Colors, Fonts, Radius, input_field


# ── Grid & kart sabitleri ─────────────────────────────────────
_CARD_W    = 348
_CARD_H    = 358
_CARD_GAP  = 18
_SIDE_PAD  = 28
_MIN_COLS  = 1
_MAX_COLS  = 3


# ════════════════════════════════════════════════════════════
#  KAMPANYA KARTI
# ════════════════════════════════════════════════════════════

class _CampaignCard(QFrame):
    """Tek bir kampanyayı gösteren premium kart — aktif/expired state destekli."""

    clicked = pyqtSignal(object)

    # Altın tonlarıyla uyumlu badge paleti
    _BADGE_COLORS = {
        "Yeni":     Colors.GREEN,        # taze/yeni — emerald
        "Popüler":  Colors.GOLD,         # klasik altın prestij
        "Sınırlı":  "#E76F51",           # bakır-kırmızı, aciliyet
        "Fırsat":   Colors.AMBER,        # amber — sıcak fırsat
        "Aktif":    Colors.GOLD_BRIGHT,  # parlak altın — aktif
        "Kampanya": Colors.GOLD,
    }

    def __init__(self, campaign: Campaign, parent=None):
        super().__init__(parent)
        self._campaign = campaign
        self._expired  = campaign.is_expired() or not campaign.is_active
        self.setFixedSize(_CARD_W, _CARD_H)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style(hovered=False)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_image_area())

        content = QWidget()
        content.setStyleSheet("background: transparent; border: none;")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(18, 14, 18, 16)
        c_lay.setSpacing(7)

        # Başlık
        title = QLabel(self._campaign.title)
        title_color = Colors.TEXT_MUTED if self._expired else Colors.TEXT_H1
        title.setStyleSheet(
            f"color: {title_color}; font-size: 15px; font-weight: 700; "
            f"border: none; background: transparent;"
        )
        title.setWordWrap(True)
        c_lay.addWidget(title)

        # Açıklama
        desc = self._campaign.description or ""
        if len(desc) > 90:
            desc = desc[:87] + "…"
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; "
            f"border: none; background: transparent;"
        )
        desc_lbl.setWordWrap(True)
        c_lay.addWidget(desc_lbl)

        c_lay.addStretch()

        # İndirim chip + geri sayım
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        discount_chip = QLabel(self._campaign.discount_label())
        if self._expired:
            chip_color, chip_bg, chip_border = Colors.TEXT_MUTED, "transparent", f"{Colors.BORDER_DEFAULT}"
        else:
            chip_color, chip_bg, chip_border = Colors.GOLD, Colors.GOLD_SUBTLE, f"{Colors.GOLD}55"
        discount_chip.setStyleSheet(f"""
            color: {chip_color};
            background: {chip_bg};
            border: 1px solid {chip_border};
            border-radius: {Radius.SM};
            padding: 5px 11px;
            font-size: 10px; font-weight: 800;
            letter-spacing: 0.4px;
        """)
        info_row.addWidget(discount_chip)
        info_row.addStretch()

        self._countdown_lbl = QLabel("")
        info_row.addWidget(self._countdown_lbl)
        c_lay.addLayout(info_row)

        # "Kampanyayı Gör" butonu
        btn_label = "Süresi Doldu" if self._expired else "Kampanyayı Gör  →"
        btn = QPushButton(btn_label)
        btn.setFixedHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setEnabled(not self._expired)
        if self._expired:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_MUTED};
                    border: 1px dashed {Colors.BORDER_DEFAULT};
                    border-radius: {Radius.SM};
                    font-size: 12px; font-weight: 600;
                    padding: 0 14px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});
                    color: {Colors.TEXT_ON_GOLD};
                    border: none;
                    border-radius: {Radius.SM};
                    font-size: 12px; font-weight: 700;
                    padding: 0 14px; letter-spacing: 0.3px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #FFD700, stop:1 {Colors.GOLD_BRIGHT});
                }}
            """)
            btn.clicked.connect(self._emit_clicked)
        c_lay.addWidget(btn)

        root.addWidget(content, 1)
        self.update_countdown()

    def _build_image_area(self) -> QWidget:
        box = QFrame()
        box.setFixedHeight(158)
        box.setObjectName("imgBox")
        box.setStyleSheet(f"""
            QFrame#imgBox {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {Colors.BG_ELEVATED}, stop:0.5 {Colors.BG_RAISED},
                    stop:1 rgba(212,175,55,0.12));
                border: none;
                border-top-left-radius: {Radius.LG};
                border-top-right-radius: {Radius.LG};
            }}
        """)

        # Görsel (fallback için emoji)
        self._img_lbl = QLabel(box)
        self._img_lbl.setGeometry(0, 0, _CARD_W, 158)
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet("background: transparent; border: none;")
        self._load_image()

        # Karartma (expired için)
        if self._expired:
            dim = QLabel(box)
            dim.setGeometry(0, 0, _CARD_W, 158)
            dim.setStyleSheet("background: rgba(8, 13, 24, 0.55); border: none;")
            dim.raise_()

        # Kategori etiketi (üst sol) — premium mini chip
        cat_txt = self._campaign.category or "Tümü"
        cat_lbl = QLabel(f"  {cat_txt}  ", box)
        cat_lbl.setStyleSheet(f"""
            background: rgba(8, 13, 24, 0.78);
            color: {Colors.GOLD};
            border: 1px solid {Colors.GOLD}44;
            border-radius: {Radius.FULL};
            padding: 4px 10px;
            font-size: 9px; font-weight: 700;
            letter-spacing: 0.4px;
        """)
        cat_lbl.adjustSize()
        cat_lbl.move(12, 12)
        cat_lbl.raise_()

        # Badge (üst sağ)
        badge_text = "BİTTİ" if self._expired else (self._campaign.badge or "")
        if badge_text:
            color = Colors.TEXT_MUTED if self._expired else self._BADGE_COLORS.get(
                self._campaign.badge, Colors.GOLD
            )
            # Altın tonlu gradient için parlak badge
            use_gold_grad = color in (Colors.GOLD, Colors.GOLD_BRIGHT)
            if use_gold_grad and not self._expired:
                bg_style = (
                    f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    f"stop:0 {Colors.GOLD_BRIGHT}, stop:1 {Colors.GOLD});"
                )
                txt_color = Colors.TEXT_ON_GOLD
            else:
                bg_style = f"background: {color};"
                txt_color = "#FFFFFF" if not self._expired else Colors.BG_BASE

            badge = QLabel(badge_text.upper(), box)
            badge.setStyleSheet(f"""
                {bg_style}
                color: {txt_color};
                border-radius: {Radius.SM};
                padding: 5px 11px;
                font-size: 9px; font-weight: 800;
                letter-spacing: 0.9px;
            """)
            badge.adjustSize()
            badge.move(_CARD_W - badge.width() - 12, 12)
            badge.raise_()

        return box

    def _load_image(self) -> None:
        path = self._campaign.image_path
        resolved: Optional[Path] = None
        if path:
            p = Path(path)
            resolved = p if p.is_absolute() else config.BASE_DIR / p
            # Bulunamazsa yaygın alternatif klasörleri dene
            if not resolved.exists():
                for alt in (
                    config.ASSETS_DIR / "campaigns" / p.name,
                    config.PRODUCT_IMAGES_DIR / p.name,
                ):
                    if alt.exists():
                        resolved = alt
                        break
                else:
                    resolved = None

        if resolved and resolved.exists():
            pix = QPixmap(str(resolved)).scaled(
                _CARD_W, 158,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_lbl.setPixmap(pix)
            return

        # ── Görsel yoksa premium fallback ───────────────────
        # Büyük kategori ikonu + indirim değeri birlikte
        cat = (self._campaign.category or "").lower()
        icon = "🎁"
        if "bilezik" in cat or "bileklik" in cat: icon = "💫"
        elif "yüzük" in cat:                      icon = "💍"
        elif "kolye" in cat:                      icon = "📿"
        elif "küpe" in cat:                       icon = "✨"
        elif "zincir" in cat:                     icon = "⛓"
        elif "set" in cat:                        icon = "💎"
        elif "erkek" in cat:                      icon = "⌚"
        elif "çocuk" in cat:                      icon = "🧸"
        elif "koleksiyon" in cat:                 icon = "🏆"

        # Fallback: büyük indirim değeri + ikon
        if self._campaign.discount_type == "percentage":
            big = f"%{self._campaign.discount_value:g}"
        elif self._campaign.discount_type == "fixed":
            big = f"₺{self._campaign.discount_value:,.0f}"
        else:
            big = "FREE"

        html = (
            f"<div style='font-family: Segoe UI;'>"
            f"<span style='font-size: 46px;'>{icon}</span><br>"
            f"<span style='color: #D4AF37; font-size: 30px; "
            f"font-weight: 800; letter-spacing: 1px;'>{big}</span>"
            f"</div>"
        )
        self._img_lbl.setText(html)
        self._img_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._img_lbl.setStyleSheet(
            "background: transparent; border: none;"
        )

    # ── Geri sayım ────────────────────────────────────────────

    def update_countdown(self) -> None:
        if self._expired:
            self._countdown_lbl.setText("⏱  SONA ERDİ")
            self._countdown_lbl.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                f"background: transparent; border: none; letter-spacing: 0.4px;"
            )
            return

        remaining = self._campaign.time_remaining()
        if remaining is None:
            self._expired = True
            self.update_countdown()
            return
        days, hours, minutes = remaining
        if days > 0:
            txt = f"⏱  {days} gün {hours}s"
            color = Colors.AMBER if days < 3 else Colors.TEXT_BODY
        elif hours > 0:
            txt = f"⏱  {hours}s {minutes}dk"
            color = Colors.RED
        else:
            txt = f"⏱  {minutes} dakika"
            color = Colors.RED
        self._countdown_lbl.setText(txt)
        self._countdown_lbl.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: 700; "
            f"background: transparent; border: none; letter-spacing: 0.3px;"
        )

    # ── Hover glow ────────────────────────────────────────────

    def _apply_style(self, hovered: bool) -> None:
        if self._expired:
            self.setStyleSheet(f"""
                _CampaignCard {{
                    background: {Colors.BG_SURFACE};
                    border: 1px dashed {Colors.BORDER_DIM};
                    border-radius: {Radius.LG};
                }}
            """)
            return

        if hovered:
            self.setStyleSheet(f"""
                _CampaignCard {{
                    background: {Colors.BG_SURFACE};
                    border: 1px solid {Colors.GOLD};
                    border-radius: {Radius.LG};
                }}
            """)
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(32)
            shadow.setColor(QColor(212, 175, 55, 130))
            shadow.setOffset(0, 0)
            self.setGraphicsEffect(shadow)
        else:
            self.setStyleSheet(f"""
                _CampaignCard {{
                    background: {Colors.BG_SURFACE};
                    border: 1px solid {Colors.BORDER_DIM};
                    border-radius: {Radius.LG};
                }}
            """)
            self.setGraphicsEffect(None)

    def enterEvent(self, event):
        if not self._expired:
            self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._expired:
            self._emit_clicked()
        super().mousePressEvent(event)

    def _emit_clicked(self) -> None:
        self.clicked.emit(self._campaign)


# ════════════════════════════════════════════════════════════
#  ÖZET KPI KARTI
# ════════════════════════════════════════════════════════════

class _SummaryCard(QFrame):
    """Üstteki özet KPI kartı — ikon + değer + etiket."""

    def __init__(self, icon: str, value: str, label: str,
                 accent: str = None, parent=None):
        super().__init__(parent)
        accent = accent or Colors.GOLD
        self.setFixedHeight(88)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-left: 3px solid {accent};
                border-radius: {Radius.LG};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(14)

        ico = QLabel(icon)
        ico.setStyleSheet(
            f"font-size: 26px; color: {accent}; "
            f"background: transparent; border: none;"
        )
        ico.setFixedWidth(38)

        col = QVBoxLayout()
        col.setSpacing(2)
        self._val = QLabel(value)
        self._val.setStyleSheet(
            f"color: {accent}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none; font-family: {Fonts.FAMILY};"
        )
        self._lbl = QLabel(label.upper())
        self._lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )
        col.addWidget(self._val)
        col.addWidget(self._lbl)

        lay.addWidget(ico)
        lay.addLayout(col)
        lay.addStretch()

    def set_value(self, value: str) -> None:
        self._val.setText(value)


# ════════════════════════════════════════════════════════════
#  KAMPANYALAR SAYFASI
# ════════════════════════════════════════════════════════════

class CampaignsPage(QWidget):
    """Aktif + süresi dolmuş kampanyaları özet + filtre ile sunar."""

    category_selected = pyqtSignal(str)

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx               = ctx
        self._all_campaigns:   list[Campaign]       = []
        self._active_cards:    list[_CampaignCard]  = []
        self._expired_cards:   list[_CampaignCard]  = []
        self._current_cols_active  = 2
        self._current_cols_expired = 2

        self._build_ui()
        self._start_countdown_timer()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        # Ana içerik kaydırılabilir
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setStyleSheet(f"background: {Colors.BG_BASE};")
        scroll.setWidget(inner)

        lay = QVBoxLayout(inner)
        lay.setContentsMargins(_SIDE_PAD, 20, _SIDE_PAD, 22)
        lay.setSpacing(18)

        lay.addWidget(self._build_summary_bar())
        lay.addWidget(self._build_filter_bar())

        # ── Aktif kampanyalar bölümü ─────────────────────────
        self._active_title = self._section_title("◆  Aktif Kampanyalar", accent=True)
        lay.addWidget(self._active_title)

        self._active_grid_w = QWidget()
        self._active_grid_w.setStyleSheet("background: transparent;")
        self._active_grid = QGridLayout(self._active_grid_w)
        self._active_grid.setContentsMargins(0, 0, 0, 0)
        self._active_grid.setSpacing(_CARD_GAP)
        self._active_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(self._active_grid_w)

        # ── Süresi dolanlar bölümü ───────────────────────────
        self._expired_title = self._section_title("◯  Süresi Dolanlar", accent=False)
        self._expired_title.hide()
        lay.addWidget(self._expired_title)

        self._expired_grid_w = QWidget()
        self._expired_grid_w.setStyleSheet("background: transparent;")
        self._expired_grid_w.hide()
        self._expired_grid = QGridLayout(self._expired_grid_w)
        self._expired_grid.setContentsMargins(0, 0, 0, 0)
        self._expired_grid.setSpacing(_CARD_GAP)
        self._expired_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(self._expired_grid_w)

        # Boş durum
        self._empty_lbl = QLabel(
            "🎁\nFiltreye uygun kampanya bulunamadı."
        )
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 14px; padding: 60px;"
        )
        self._empty_lbl.hide()
        lay.addWidget(self._empty_lbl)

        lay.addStretch()
        root.addWidget(scroll, 1)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(72)
        w.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {Colors.BG_RAISED},
                    stop:1 rgba(212,175,55,0.10));
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(_SIDE_PAD, 0, _SIDE_PAD, 0)
        lay.setSpacing(12)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("🎁  Kampanyalar & Fırsatlar")
        t.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; border: none;"
        )
        s = QLabel("Özel indirimler ve sınırlı süreli teklifler")
        s.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        col.addWidget(t)
        col.addWidget(s)
        lay.addLayout(col)
        lay.addStretch()

        self._count_pill = QLabel("●  YÜKLENİYOR")
        self._count_pill.setFixedHeight(32)
        self._count_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_pill.setStyleSheet(f"""
            color: {Colors.GOLD};
            background: {Colors.GOLD_SUBTLE};
            border: 1px solid {Colors.GOLD}60;
            border-radius: 16px;
            padding: 0 14px;
            font-size: 10px; font-weight: 800;
            letter-spacing: 0.8px;
        """)
        lay.addWidget(self._count_pill, alignment=Qt.AlignmentFlag.AlignVCenter)
        return w

    # ── Özet KPI satırı ───────────────────────────────────────

    def _build_summary_bar(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self._sum_active  = _SummaryCard("●",  "0", "Aktif Kampanya",    Colors.GREEN)
        self._sum_ending  = _SummaryCard("⏰", "0", "24 Saat İçinde Biten", Colors.AMBER)
        self._sum_maxdisc = _SummaryCard("🔥", "—", "En Yüksek İndirim",  Colors.GOLD)

        for card in (self._sum_active, self._sum_ending, self._sum_maxdisc):
            lay.addWidget(card, 1)
        return w

    # ── Arama + badge filtresi ────────────────────────────────

    def _build_filter_bar(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Kampanya ara…  (başlık veya açıklama)")
        self._search.setFixedHeight(40)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.BG_INPUT}; color: {Colors.TEXT_H1};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.FULL};
                padding: 0 18px; font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {Colors.GOLD}; background: {Colors.BG_ELEVATED};
            }}
            QLineEdit::placeholder {{ color: {Colors.TEXT_MUTED}; }}
        """)
        self._search.textChanged.connect(self._apply_filters)

        self._badge_cb = QComboBox()
        self._badge_cb.setFixedSize(180, 40)
        self._badge_cb.setStyleSheet(input_field())
        self._badge_cb.addItem("Tüm Etiketler", None)
        for b in ("Yeni", "Popüler", "Sınırlı", "Fırsat", "Aktif", "Kampanya"):
            self._badge_cb.addItem(b, b)
        self._badge_cb.currentIndexChanged.connect(self._apply_filters)

        lay.addWidget(self._search, 1)
        lay.addWidget(self._badge_cb)
        return w

    def _section_title(self, text: str, accent: bool = True) -> QLabel:
        color = Colors.GOLD if accent else Colors.TEXT_MUTED
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 800; "
            f"letter-spacing: 1.4px; border: none; padding: 6px 0 2px 0;"
        )
        return lbl

    # ── Responsive grid ───────────────────────────────────────

    def _compute_cols(self) -> int:
        w = self.width() - (_SIDE_PAD * 2)
        if w <= _CARD_W:
            return _MIN_COLS
        cols = (w + _CARD_GAP) // (_CARD_W + _CARD_GAP)
        return max(_MIN_COLS, min(_MAX_COLS, int(cols)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cols = self._compute_cols()
        needs_relayout = False
        if cols != self._current_cols_active:
            self._current_cols_active = cols
            needs_relayout = True
        if cols != self._current_cols_expired:
            self._current_cols_expired = cols
            needs_relayout = True
        if needs_relayout and (self._active_cards or self._expired_cards):
            self._apply_filters()

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        # get_active_campaigns() otomatik expired'ları pasifleştirir
        self._ctx.campaign_service.get_active_campaigns()
        self._all_campaigns = self._ctx.campaign_service.get_all()

        # Eski kartları grid'den çıkar + sil
        while self._active_grid.count():
            self._active_grid.takeAt(0)
        while self._expired_grid.count():
            self._expired_grid.takeAt(0)
        for card in self._active_cards + self._expired_cards:
            card.setParent(None)
            card.deleteLater()
        self._active_cards.clear()
        self._expired_cards.clear()

        cols = self._compute_cols()
        self._current_cols_active  = cols
        self._current_cols_expired = cols

        actives  = [c for c in self._all_campaigns if c.is_active and not c.is_expired()]
        expireds = [c for c in self._all_campaigns if (not c.is_active) or c.is_expired()]

        # Kartları doğru parent ile oluştur, LİSTEYE ekle (grid'e filter sırasında eklenir)
        for c in actives:
            card = _CampaignCard(c, parent=self._active_grid_w)
            card.clicked.connect(self._on_campaign_clicked)
            self._active_cards.append(card)

        for c in expireds:
            card = _CampaignCard(c, parent=self._expired_grid_w)
            self._expired_cards.append(card)

        self._update_summary(actives, expireds)
        self._apply_filters()

    # ── Özet güncelle ─────────────────────────────────────────

    def _update_summary(self, actives: list[Campaign], expireds: list[Campaign]) -> None:
        self._sum_active.set_value(str(len(actives)))

        # 24 saat içinde bitenler
        now = datetime.now()
        ending_soon = 0
        for c in actives:
            rem = c.time_remaining(now)
            if rem is None:
                continue
            days, hours, _ = rem
            if days == 0 and hours <= 24:
                ending_soon += 1
        self._sum_ending.set_value(str(ending_soon))

        # En yüksek indirim oranı (percentage)
        pct_values = [c.discount_value for c in actives if c.discount_type == "percentage"]
        if pct_values:
            self._sum_maxdisc.set_value(f"%{max(pct_values):g}")
        else:
            self._sum_maxdisc.set_value("—")

        # Üstteki pill
        total_active = len(actives)
        self._count_pill.setText(f"● {total_active} AKTİF KAMPANYA")

    # ── Filtre uygula ─────────────────────────────────────────

    def _apply_filters(self) -> None:
        query        = self._search.text().strip().lower()
        badge_filter = self._badge_cb.currentData()

        def matches(c: Campaign) -> bool:
            if query:
                hay = (c.title + " " + (c.description or "")).lower()
                if query not in hay:
                    return False
            if badge_filter and c.badge != badge_filter:
                return False
            return True

        # Grid'lerden tüm kartları çıkar (widget'lar silinmez, sadece layout'tan)
        while self._active_grid.count():
            self._active_grid.takeAt(0)
        while self._expired_grid.count():
            self._expired_grid.takeAt(0)

        # Tümünü gizle — sonra eşleşenleri ekleyerek göstereceğiz
        for card in self._active_cards + self._expired_cards:
            card.setVisible(False)

        # Aktif kampanyalar
        cols_a = max(1, self._current_cols_active)
        visible_active = 0
        for card in self._active_cards:
            if matches(card._campaign):
                self._active_grid.addWidget(
                    card, visible_active // cols_a, visible_active % cols_a
                )
                card.setVisible(True)
                visible_active += 1

        # Süresi dolanlar
        cols_e = max(1, self._current_cols_expired)
        visible_expired = 0
        for card in self._expired_cards:
            if matches(card._campaign):
                self._expired_grid.addWidget(
                    card, visible_expired // cols_e, visible_expired % cols_e
                )
                card.setVisible(True)
                visible_expired += 1

        # Bölüm başlıklarını göster/gizle
        self._active_title.setVisible(visible_active > 0)
        self._active_grid_w.setVisible(visible_active > 0)
        self._expired_title.setVisible(visible_expired > 0)
        self._expired_grid_w.setVisible(visible_expired > 0)

        self._empty_lbl.setVisible(visible_active + visible_expired == 0)

    # ── Geri sayım timer (60 sn) ─────────────────────────────

    def _start_countdown_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_countdowns)
        self._timer.start(60_000)

    def _tick_countdowns(self) -> None:
        any_expired_now = False
        for card in self._active_cards:
            if card._campaign.is_expired():
                any_expired_now = True
            card.update_countdown()
        # Biten kampanya varsa tüm listeyi yenile (expired bölümüne taşı)
        if any_expired_now:
            self.refresh()

    # ── Tıklama → katalog filtresi ────────────────────────────

    def _on_campaign_clicked(self, campaign: Campaign) -> None:
        cats = campaign.categories_list()
        target = cats[0] if cats else ""
        self.category_selected.emit(target)
