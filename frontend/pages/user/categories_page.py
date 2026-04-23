"""
Kategoriler Sayfası — gruplu "Shop by Category" deneyimi.

Her ana kategori (YÜZÜK, KOLYE, KÜPE …) ayrı bir bölüm olarak gösterilir.
Her bölümde altta alt kategori chip'leri bulunur.
Chip'e tıklanınca katalog sayfası ilgili kategori + alt kategori ile açılır.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.app_context import AppContext
from frontend.styles.app_theme import Colors, Radius
from frontend.utils import product_subcategory


_SIDE_PAD = 28


# ── Bölüm tanımları (ana kategori + altına giren DB kategorileri) ──
# Eğer use_cats_as_subs=True ise alt kategori olarak DB'deki kategori
# isimleri kullanılır (altın için). Aksi halde ürün description'larından
# "Alt: X" değerleri toplanır.
SECTIONS = [
    {"name": "Yüzük",              "icon": "💍", "cats": ["Yüzük"],              "use_cats_as_subs": False},
    {"name": "Kolye",              "icon": "📿", "cats": ["Kolye"],              "use_cats_as_subs": False},
    {"name": "Küpe",               "icon": "👂", "cats": ["Küpe"],               "use_cats_as_subs": False},
    {"name": "Bilezik",            "icon": "🟡", "cats": ["Bilezik"],            "use_cats_as_subs": False},
    {"name": "Bileklik",           "icon": "🔗", "cats": ["Bileklik"],           "use_cats_as_subs": False},
    {"name": "Zincir",             "icon": "⛓",  "cats": ["Zincir"],             "use_cats_as_subs": False},
    {"name": "Set",                "icon": "💎", "cats": ["Set"],                "use_cats_as_subs": False},
    {"name": "Altın (Yatırımlık)", "icon": "🪙",
        "cats": ["Çeyrek Altın", "Yarım Altın", "Tam Altın",
                 "Ata Altın", "Ziynet Altın", "Gram Altın"],
        "use_cats_as_subs": True},
    {"name": "Erkek Koleksiyonu",  "icon": "🧔", "cats": ["Erkek Koleksiyonu"],  "use_cats_as_subs": False},
    {"name": "Çocuk Takıları",     "icon": "👶", "cats": ["Çocuk Takıları"],     "use_cats_as_subs": False},
    {"name": "Özel Tasarım",       "icon": "✨", "cats": ["Özel Tasarım"],       "use_cats_as_subs": False},
]


# ════════════════════════════════════════════════════════════
#  BÖLÜM WIDGET'I
# ════════════════════════════════════════════════════════════

class _SectionFrame(QFrame):
    """Tek bir ana kategori bölümü — başlık + alt kategori chip satırı."""

    # category_name, subcategory_name (subcategory boş olabilir)
    chip_clicked = pyqtSignal(str, str)

    def __init__(self, section: dict, products: list, parent=None):
        super().__init__(parent)
        self._section = section
        self._products = products
        self._setup_style()
        self._build_ui()

    def _setup_style(self) -> None:
        self.setStyleSheet(f"""
            _SectionFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DIM};
                border-left: 3px solid {Colors.GOLD_DIM};
                border-radius: {Radius.LG};
            }}
            _SectionFrame:hover {{
                border-left-color: {Colors.GOLD};
            }}
        """)

    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 18)
        lay.setSpacing(10)

        # ── Başlık satırı ─────────────────────────────────────
        head = QHBoxLayout()
        head.setSpacing(12)

        icon = QLabel(self._section["icon"])
        icon.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        icon.setFixedWidth(36)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)
        title = QLabel(self._section["name"].upper())
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 14px; font-weight: 800; "
            f"letter-spacing: 1.2px; background: transparent; border: none;"
        )
        count_txt = self._count_text()
        sub = QLabel(count_txt)
        sub.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.4px; background: transparent; border: none;"
        )
        title_col.addWidget(title)
        title_col.addWidget(sub)

        head.addWidget(icon)
        head.addLayout(title_col)
        head.addStretch()

        # Tümünü gör → ana kategori filtresi
        btn_all = QPushButton("Tümünü Gör  →")
        btn_all.setFixedHeight(30)
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.GOLD};
                border: 1px solid {Colors.GOLD}55; border-radius: {Radius.FULL};
                font-size: 11px; font-weight: 600; padding: 0 14px;
            }}
            QPushButton:hover {{
                background: {Colors.GOLD_SUBTLE}; border-color: {Colors.GOLD};
            }}
        """)
        btn_all.clicked.connect(
            lambda: self.chip_clicked.emit(self._primary_category(), "")
        )
        head.addWidget(btn_all)
        lay.addLayout(head)

        # ── Alt kategori chip'leri ────────────────────────────
        chips_row = self._build_chips_row()
        lay.addLayout(chips_row)

    def _count_text(self) -> str:
        total = len(self._products)
        return f"● {total} ürün" if total else "— ürün yok"

    def _primary_category(self) -> str:
        return self._section["cats"][0] if self._section["cats"] else ""

    # ── Alt kategori chip'leri ────────────────────────────────

    def _build_chips_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(7)
        row.setContentsMargins(0, 2, 0, 2)
        row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        chips = self._collect_subcategories()
        if not chips:
            empty = QLabel("Bu kategoride henüz ürün yok")
            empty.setStyleSheet(
                f"color: {Colors.TEXT_MUTED}; font-size: 11px; "
                f"background: transparent; border: none;"
            )
            row.addWidget(empty)
            return row

        for sub_label, (cat_for_chip, sub_value) in chips:
            btn = self._make_chip(sub_label)
            btn.clicked.connect(
                lambda _, c=cat_for_chip, s=sub_value:
                    self.chip_clicked.emit(c, s)
            )
            row.addWidget(btn)
        row.addStretch()
        return row

    def _collect_subcategories(self) -> list[tuple[str, tuple[str, str]]]:
        """
        Döner: [(görünen_etiket, (filtre_kategorisi, filtre_alt_kategorisi))]
        """
        if self._section.get("use_cats_as_subs"):
            # ALTIN bölümü → her kategoriyi alt-chip olarak göster
            result = []
            seen = set()
            for cat_name in self._section["cats"]:
                hits = [p for p in self._products if (p.category_name or "") == cat_name]
                if hits and cat_name not in seen:
                    seen.add(cat_name)
                    # Kısaltılmış görünüm (örn. "Çeyrek Altın" → "Çeyrek")
                    short = cat_name.replace(" Altın", "").strip()
                    result.append((short, (cat_name, "")))
            return result

        # Diğer bölümler → description'dan "Alt: X"
        seen = set()
        result: list[tuple[str, tuple[str, str]]] = []
        primary = self._primary_category()
        for p in self._products:
            sub = product_subcategory(p)
            if sub and sub not in seen:
                seen.add(sub)
                result.append((sub, (primary, sub)))
        return result

    def _make_chip(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.FULL};
                font-size: 11px; font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {Colors.GOLD_SUBTLE};
                color: {Colors.GOLD};
                border-color: {Colors.GOLD}88;
            }}
            QPushButton:pressed {{
                background: rgba(212,175,55,0.20);
            }}
        """)
        return btn


# ════════════════════════════════════════════════════════════
#  KATEGORİLER SAYFASI
# ════════════════════════════════════════════════════════════

class CategoriesPage(QWidget):

    # (category_name, subcategory_name) — subcategory boş olursa sadece kat. filtresi
    category_selected = pyqtSignal(str, str)

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._section_widgets: list[_SectionFrame] = []
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        inner = QWidget()
        inner.setStyleSheet(f"background: {Colors.BG_BASE};")
        self._inner_lay = QVBoxLayout(inner)
        self._inner_lay.setContentsMargins(_SIDE_PAD, 22, _SIDE_PAD, 24)
        self._inner_lay.setSpacing(12)
        self._inner_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(inner)
        root.addWidget(scroll, 1)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(72)
        w.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {Colors.BG_RAISED}, stop:1 rgba(212,175,55,0.10));
                border-bottom: 1px solid {Colors.BORDER_DEFAULT};
            }}
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(_SIDE_PAD, 0, _SIDE_PAD, 0)

        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("🏷  Kategoriler")
        t.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 18px; font-weight: 700; border: none;"
        )
        s = QLabel("Ürünleri kategoriye ve alt kategoriye göre keşfedin")
        s.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; border: none;"
        )
        col.addWidget(t)
        col.addWidget(s)
        lay.addLayout(col)
        lay.addStretch()

        self._count_pill = QLabel("")
        self._count_pill.setFixedHeight(30)
        self._count_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._count_pill.setStyleSheet(f"""
            color: {Colors.GOLD};
            background: {Colors.GOLD_SUBTLE};
            border: 1px solid {Colors.GOLD}60;
            border-radius: 15px;
            padding: 0 14px;
            font-size: 10px; font-weight: 800; letter-spacing: 0.8px;
        """)
        lay.addWidget(self._count_pill, alignment=Qt.AlignmentFlag.AlignVCenter)
        return w

    # ── Veri yükleme ──────────────────────────────────────────

    def refresh(self) -> None:
        # Önceki bölümleri temizle
        for w in self._section_widgets:
            w.setParent(None)
            w.deleteLater()
        self._section_widgets.clear()
        while self._inner_lay.count():
            item = self._inner_lay.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        all_products = self._ctx.product_service.get_all(for_sale_only=False)

        # Kategori adı → ürün listesi map'i
        products_by_cat: dict[str, list] = {}
        for p in all_products:
            products_by_cat.setdefault(p.category_name or "", []).append(p)

        total_sections = 0
        for section in SECTIONS:
            # Bu bölüme giren tüm ürünler
            section_products = []
            for cname in section["cats"]:
                section_products.extend(products_by_cat.get(cname, []))

            # Ürünü olmayan bölümü gizle
            if not section_products:
                continue

            frame = _SectionFrame(section, section_products)
            frame.chip_clicked.connect(self.category_selected.emit)
            self._inner_lay.addWidget(frame)
            self._section_widgets.append(frame)
            total_sections += 1

        self._inner_lay.addStretch()
        self._count_pill.setText(f"{total_sections} BÖLÜM")
