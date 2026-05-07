"""
CheckoutPage — Ödemeye geç akışı.

Sepetteki ürünler kullanıcıya gösterilir, ödeme yöntemi seçtirilir, gerekli
formlar doldurulur ve "Siparişi Tamamla" basıldığında OrderService üzerinden
sipariş oluşturulur.

Sayfa, Sepet sayfasından `start(...)` çağrısı ile başlatılır. UserWindow
bu sayfa üzerinde `order_completed` sinyalini dinler.
"""

import re
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QButtonGroup, QLineEdit, QComboBox, QStackedWidget, QScrollArea,
    QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from backend.app_context import AppContext
from backend.models.saved_card import SavedCard
from backend.services.order_service import (
    SHIPPING_FREE_THRESHOLD, calculate_shipping,
)
from frontend.styles.app_theme import Colors, Fonts, Radius, gold_btn, input_field
from frontend.components.toast import Toast
from frontend.dialogs.saved_cards_dialog import SavedCardsDialog


_PAYMENT_METHODS = [
    ("card",     "💳", "Kredi / Banka Kartı", "Anında ödeme — 3D Secure"),
    ("transfer", "🏦", "Havale / EFT",        "IBAN'a transfer sonrası onaylanır"),
    ("cod",      "📦", "Kapıda Ödeme",        "Teslimatta nakit / kart"),
    ("pickup",   "🏪", "Mağazadan Teslim",   "Seçtiğiniz mağazadan alın"),
]

_STORES = [
    "Kapalıçarşı Şubesi  ·  İstanbul",
    "Nişantaşı Şubesi  ·  İstanbul",
    "Bağdat Caddesi Şubesi  ·  İstanbul",
    "Kızılay Şubesi  ·  Ankara",
    "Alsancak Şubesi  ·  İzmir",
]

# Demo IBAN — gerçek hesap bilgisi değildir
_DEMO_IBAN = "TR12 0001 2345 6789 0123 4567 89"
_DEMO_BANK = "Kuyumcu Pro Anonim Şirketi  ·  Ziraat Bankası"


class CheckoutPage(QWidget):
    """Ödeme sayfası."""

    order_completed = pyqtSignal(object)   # Order
    back_to_cart    = pyqtSignal()

    def __init__(self, ctx: AppContext):
        super().__init__()
        self._ctx = ctx
        self._items: list[dict]   = []
        self._unit_prices: dict[int, float] = {}
        self._method: str = "card"
        self._saved_cards: list[SavedCard] = []
        self._selected_card: Optional[SavedCard] = None  # None → yeni kart formu
        self._card_buttons: list[QPushButton] = []
        self._build_ui()

    # ── Public API ────────────────────────────────────────────

    def start(self) -> None:
        """Sepet sayfasından çağrılır — verileri yükle ve sayfayı tazele."""
        self.refresh()

    def refresh(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            return
        self._items = self._ctx.cart_service.get_cart_items(user.id)

        if not self._items:
            # Sepet boşaldıysa kullanıcıya bilgi ver, sepet sayfasına yönlendir
            self.back_to_cart.emit()
            return

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        self._unit_prices = {
            it["product"].id: self._ctx.price_calculator.calculate(it["product"], gold)
            for it in self._items
        }
        self._render_summary()
        self._reload_saved_cards()

    # ── UI ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # Üst: başlık + geri buton
        head = QHBoxLayout()
        back = QPushButton("←  Sepete Dön")
        back.setFixedHeight(36)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT}; border-radius: {Radius.SM};
                padding: 0 16px; font-size: 12px;
            }}
            QPushButton:hover {{ color: {Colors.GOLD}; border-color: {Colors.GOLD}; }}
        """)
        back.clicked.connect(self.back_to_cart.emit)
        head.addWidget(back)

        title = QLabel("💳  Ödeme")
        title.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 20px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        head.addSpacing(14)
        head.addWidget(title)
        head.addStretch()
        root.addLayout(head)

        # İçerik: solda yöntem + form, sağda özet
        content = QHBoxLayout()
        content.setSpacing(16)

        content.addWidget(self._build_left_panel(), 2)
        content.addWidget(self._build_right_summary(), 1)
        root.addLayout(content, 1)

    # ── SOL: Yöntem seçimi + dinamik form ────────────────────

    def _build_left_panel(self) -> QWidget:
        wrap = QFrame()
        wrap.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.LG};
            }}
        """)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)

        h = QLabel("Ödeme Yöntemi")
        h.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        lay.addWidget(h)

        # Yöntem kartları
        self._method_group = QButtonGroup(self)
        self._method_group.setExclusive(True)
        method_grid = QGridLayout()
        method_grid.setSpacing(10)
        for i, (code, ico, label, hint) in enumerate(_PAYMENT_METHODS):
            btn = self._method_card(code, ico, label, hint)
            self._method_group.addButton(btn, i)
            method_grid.addWidget(btn, i // 2, i % 2)
        lay.addLayout(method_grid)
        lay.addSpacing(6)

        # Dinamik form alanı (yönteme göre değişir)
        self._form_stack = QStackedWidget()
        self._form_stack.addWidget(self._build_card_form())     # 0 — card
        self._form_stack.addWidget(self._build_transfer_form()) # 1 — transfer
        self._form_stack.addWidget(self._build_cod_form())      # 2 — cod
        self._form_stack.addWidget(self._build_pickup_form())   # 3 — pickup
        lay.addWidget(self._form_stack)

        # Hata etiketi
        self._error_lbl = QLabel("")
        self._error_lbl.setWordWrap(True)
        self._error_lbl.setStyleSheet(
            f"color: {Colors.RED}; font-size: 12px; background: transparent; border: none;"
        )
        lay.addWidget(self._error_lbl)

        lay.addStretch()
        return wrap

    def _method_card(self, code: str, ico: str, label: str, hint: str) -> QPushButton:
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(72)
        btn.setText(f"  {ico}    {label}\n         {hint}")
        btn.setStyleSheet(self._method_btn_style(False))
        btn.setChecked(code == "card")
        btn.toggled.connect(lambda on, c=code: on and self._on_method_change(c))
        # Buton stili checked durumda farklı görünsün
        btn.toggled.connect(lambda on, b=btn: b.setStyleSheet(self._method_btn_style(on)))
        return btn

    def _method_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: {Colors.GOLD_SUBTLE};
                    color: {Colors.TEXT_H1};
                    border: 2px solid {Colors.GOLD};
                    border-radius: {Radius.MD};
                    text-align: left; padding: 10px 14px;
                    font-size: 13px; font-weight: 600;
                    font-family: {Fonts.FAMILY};
                }}
            """
        return f"""
            QPushButton {{
                background: {Colors.BG_RAISED};
                color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD};
                text-align: left; padding: 10px 14px;
                font-size: 13px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{ border-color: {Colors.GOLD}; color: {Colors.TEXT_H1}; }}
        """

    def _on_method_change(self, code: str) -> None:
        self._method = code
        idx_map = {"card": 0, "transfer": 1, "cod": 2, "pickup": 3}
        self._form_stack.setCurrentIndex(idx_map[code])
        self._error_lbl.setText("")

    # ── Form — Kredi Kartı ───────────────────────────────────

    def _build_card_form(self) -> QWidget:
        wrap = QWidget()
        outer = QVBoxLayout(wrap)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)

        # ── Kayıtlı kartlar şeridi ────────────────────────────
        self._cards_section = QWidget()
        cs_lay = QVBoxLayout(self._cards_section)
        cs_lay.setContentsMargins(0, 0, 0, 0)
        cs_lay.setSpacing(6)

        head_row = QHBoxLayout()
        head_row.setSpacing(8)
        cs_head = QLabel("Kayıtlı Kartlarım")
        cs_head.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 12px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        head_row.addWidget(cs_head)
        head_row.addStretch()

        manage_btn = QPushButton("Kartları Yönet  ⚙")
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.GOLD};
                border: none; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {Colors.GOLD_BRIGHT}; }}
        """)
        manage_btn.clicked.connect(self._open_cards_manager)
        head_row.addWidget(manage_btn)
        cs_lay.addLayout(head_row)

        # Yatay scroll — chip yüksekliği 96, scroll 110 (scrollbar+padding payı)
        self._cards_scroll = QScrollArea()
        self._cards_scroll.setWidgetResizable(True)
        self._cards_scroll.setFixedHeight(112)
        self._cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cards_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        self._cards_strip = QWidget()
        self._cards_strip.setStyleSheet("background: transparent;")
        self._cards_strip_lay = QHBoxLayout(self._cards_strip)
        self._cards_strip_lay.setContentsMargins(2, 2, 2, 2)
        self._cards_strip_lay.setSpacing(8)
        self._cards_strip_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._cards_scroll.setWidget(self._cards_strip)
        cs_lay.addWidget(self._cards_scroll)

        outer.addWidget(self._cards_section)

        # ── Kart formu — alan-grupları (label + input) ────────

        self._card_holder = self._line_edit("ÖRN. AHMET YILMAZ")
        self._card_number = self._line_edit("4242 4242 4242 4242")
        self._card_expiry = self._line_edit("AA/YY")
        self._card_cvv    = self._line_edit("123")
        self._card_cvv.setEchoMode(QLineEdit.EchoMode.Password)
        self._card_cvv.setMaxLength(3)

        self._card_number.textChanged.connect(self._format_card_number)
        self._card_expiry.textChanged.connect(self._format_expiry)

        # Her alan için dedicated container (label üstte, input altta, sabit yükseklikli)
        self._holder_group = self._field_group("KART ÜZERİNDEKİ İSİM", self._card_holder)
        self._number_group = self._field_group("KART NUMARASI",        self._card_number)
        self._expiry_group = self._field_group("SON KULLANMA",         self._card_expiry)
        self._cvv_group    = self._field_group("CVV",                  self._card_cvv)

        outer.addWidget(self._holder_group)
        outer.addWidget(self._number_group)

        # Son kullanma + CVV yan yana — eşit genişlikte
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)
        bottom_row.addWidget(self._expiry_group, 1)
        bottom_row.addWidget(self._cvv_group,    1)
        outer.addLayout(bottom_row)

        # Kayıtlı kart seçildiğinde gösterilen kart bilgisi özet kutusu
        self._selected_card_lbl = QLabel("")
        self._selected_card_lbl.setWordWrap(True)
        self._selected_card_lbl.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 12px; "
            f"background: {Colors.BG_RAISED}; border: 1px dashed {Colors.GOLD}55; "
            f"border-radius: {Radius.SM}; padding: 10px 14px;"
        )
        self._selected_card_lbl.hide()
        outer.addWidget(self._selected_card_lbl)

        # "Bu kartı kaydet" + kart adı
        save_row = QHBoxLayout()
        save_row.setSpacing(10)
        self._save_card_cb = QCheckBox("Bu kartı sonraki ödemeler için kaydet")
        self._save_card_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_BODY}; font-size: 12px;
                background: transparent; border: none;
            }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 3px; background: {Colors.BG_INPUT};
            }}
            QCheckBox::indicator:checked {{
                background: {Colors.GOLD}; border-color: {Colors.GOLD};
            }}
        """)
        save_row.addWidget(self._save_card_cb)
        save_row.addStretch()
        self._save_title_input = self._line_edit("Kart adı (örn. İş Kartım)")
        self._save_title_input.setFixedWidth(200)
        self._save_title_input.setEnabled(False)
        save_row.addWidget(self._save_title_input)
        self._save_card_cb.toggled.connect(self._save_title_input.setEnabled)
        outer.addLayout(save_row)

        outer.addStretch()
        return wrap

    def _field_group(self, label_text: str, input_widget: QWidget) -> QWidget:
        """Label üstte, input altta, sabit yükseklikli temiz container."""
        w = QWidget()
        w.setMinimumHeight(64)  # 18 (label) + 6 (gap) + 40 (input)
        w.setStyleSheet("background: transparent;")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        l = QLabel(label_text)
        l.setFixedHeight(16)
        l.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.6px; background: transparent; border: none;"
        )
        v.addWidget(l)
        v.addWidget(input_widget)
        return w

    def _format_card_number(self, raw: str) -> None:
        digits = re.sub(r"\D", "", raw)[:16]
        groups = [digits[i:i + 4] for i in range(0, len(digits), 4)]
        formatted = " ".join(groups)
        if formatted != raw:
            cur = self._card_number.cursorPosition()
            self._card_number.blockSignals(True)
            self._card_number.setText(formatted)
            self._card_number.setCursorPosition(min(len(formatted), cur + 1))
            self._card_number.blockSignals(False)

    def _format_expiry(self, raw: str) -> None:
        digits = re.sub(r"\D", "", raw)[:4]
        if len(digits) >= 3:
            formatted = digits[:2] + "/" + digits[2:]
        else:
            formatted = digits
        if formatted != raw:
            self._card_expiry.blockSignals(True)
            self._card_expiry.setText(formatted)
            self._card_expiry.blockSignals(False)

    # ── Form — Havale/EFT ────────────────────────────────────

    def _build_transfer_form(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_RAISED};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)

        head = QLabel("Banka Bilgileri")
        head.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;"
        )
        lay.addWidget(head)

        bank = QLabel(_DEMO_BANK)
        bank.setStyleSheet(f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600;")
        lay.addWidget(bank)

        iban = QLabel(_DEMO_IBAN)
        iban.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 16px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY_M}; letter-spacing: 1px;"
        )
        iban.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(iban)

        info = QLabel(
            "ℹ  Açıklama alanına sipariş numaranızı yazınız.\n"
            "    Ödeme sonrası siparişiniz onaylanacaktır."
        )
        info.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 11px; padding-top: 6px;"
        )
        info.setWordWrap(True)
        lay.addWidget(info)
        lay.addStretch()
        return w

    # ── Form — Kapıda Ödeme ──────────────────────────────────

    def _build_cod_form(self) -> QWidget:
        w = QFrame()
        w.setStyleSheet(f"""
            QFrame {{
                background: {Colors.AMBER}11;
                border: 1px solid {Colors.AMBER}55;
                border-radius: {Radius.MD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        head = QLabel("⚠  Önemli Bilgi")
        head.setStyleSheet(
            f"color: {Colors.AMBER}; font-size: 13px; font-weight: 700;"
        )
        lay.addWidget(head)

        msg = QLabel(
            "Kapıda ödeme seçilmiştir. Değerli ürünlerde teslimat sırasında "
            "kimlik doğrulama gerekebilir. Lütfen geçerli bir kimlik bulundurunuz."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"color: {Colors.TEXT_BODY}; font-size: 12px; padding-top: 4px;"
        )
        lay.addWidget(msg)
        lay.addStretch()
        return w

    # ── Form — Mağazadan Teslim ──────────────────────────────

    def _build_pickup_form(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        l = QLabel("TESLİM ALACAĞINIZ MAĞAZA")
        l.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.6px; background: transparent; border: none;"
        )
        lay.addWidget(l)

        self._pickup_cb = QComboBox()
        self._pickup_cb.setFixedHeight(40)
        self._pickup_cb.setStyleSheet(input_field())
        self._pickup_cb.addItems(_STORES)
        lay.addWidget(self._pickup_cb)
        lay.addStretch()
        return w

    # ── SAĞ: Sipariş Özeti ───────────────────────────────────

    def _build_right_summary(self) -> QWidget:
        wrap = QFrame()
        wrap.setMinimumWidth(320)
        wrap.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BG_SURFACE};
                border: 1px solid {Colors.GOLD}33;
                border-radius: {Radius.LG};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(10)

        h = QLabel("📋  Sipariş Özeti")
        h.setStyleSheet(
            f"color: {Colors.GOLD}; font-size: 14px; font-weight: 700;"
        )
        lay.addWidget(h)
        lay.addSpacing(4)

        # Ürün listesi (mini scroll)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setMaximumHeight(220)
        self._items_w = QWidget()
        self._items_w.setStyleSheet("background: transparent;")
        self._items_lay = QVBoxLayout(self._items_w)
        self._items_lay.setContentsMargins(0, 0, 0, 0)
        self._items_lay.setSpacing(6)
        self._items_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._items_w)
        lay.addWidget(scroll)

        # Ayraç
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {Colors.BORDER_DEFAULT};")
        lay.addWidget(sep)

        # Toplamlar
        self._sub_lbl  = self._summary_row(lay, "Ara Toplam",         "₺ 0,00")
        self._ship_lbl = self._summary_row(lay, "Kargo / Sigorta",    "₺ 0,00")

        # Ücretsiz kargo bilgisi
        self._free_hint = QLabel("")
        self._free_hint.setStyleSheet(
            f"color: {Colors.GREEN}; font-size: 10px; font-weight: 600;"
        )
        lay.addWidget(self._free_hint)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {Colors.BORDER_DEFAULT};")
        lay.addWidget(sep2)

        # Genel toplam
        total_row = QHBoxLayout()
        total_row.setSpacing(10)
        t_l = QLabel("Genel Toplam")
        t_l.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 700;"
        )
        self._grand_lbl = QLabel("₺ 0,00")
        self._grand_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._grand_lbl.setStyleSheet(
            f"color: {Colors.GOLD_BRIGHT}; font-size: 22px; font-weight: 800; "
            f"font-family: {Fonts.FAMILY};"
        )
        total_row.addWidget(t_l)
        total_row.addStretch()
        total_row.addWidget(self._grand_lbl)
        lay.addLayout(total_row)
        lay.addSpacing(4)

        self._btn_finish = QPushButton("  ✓  Siparişi Tamamla")
        self._btn_finish.setFixedHeight(48)
        self._btn_finish.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_finish.setStyleSheet(gold_btn())
        self._btn_finish.clicked.connect(self._submit)
        lay.addWidget(self._btn_finish)

        return wrap

    def _summary_row(self, parent_lay: QVBoxLayout, label: str, value: str) -> QLabel:
        row = QHBoxLayout()
        row.setSpacing(10)
        l = QLabel(label)
        l.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 12px;")
        v = QLabel(value)
        v.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600; "
            f"font-family: {Fonts.FAMILY};"
        )
        v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(l)
        row.addStretch()
        row.addWidget(v)
        parent_lay.addLayout(row)
        return v

    # ── Render & hesap ───────────────────────────────────────

    def _render_summary(self) -> None:
        # Ürünler
        while self._items_lay.count():
            item = self._items_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        subtotal = 0.0
        for it in self._items:
            p   = it["product"]
            qty = it["quantity"]
            unit = self._unit_prices.get(p.id, 0.0)
            subtotal += unit * qty

            row = QHBoxLayout()
            row.setSpacing(8)
            name = QLabel(f"{p.name}  ×{qty}")
            name.setStyleSheet(
                f"color: {Colors.TEXT_BODY}; font-size: 12px; "
                f"background: transparent; border: none;"
            )
            name.setWordWrap(True)
            price = QLabel(f"₺ {unit * qty:,.2f}")
            price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            price.setStyleSheet(
                f"color: {Colors.TEXT_H1}; font-size: 12px; font-weight: 600; "
                f"background: transparent; border: none;"
            )
            row.addWidget(name, 1)
            row.addWidget(price)
            wrapper = QWidget()
            wrapper.setLayout(row)
            self._items_lay.addWidget(wrapper)

        shipping = calculate_shipping(subtotal)
        total    = subtotal + shipping

        self._sub_lbl.setText(f"₺ {subtotal:,.2f}")
        if shipping > 0:
            self._ship_lbl.setText(f"₺ {shipping:,.2f}")
            remaining = SHIPPING_FREE_THRESHOLD - subtotal
            self._free_hint.setText(
                f"₺ {remaining:,.0f} daha alın → ücretsiz sigortalı teslimat"
            )
        else:
            self._ship_lbl.setText("Ücretsiz")
            self._free_hint.setText("✓ Sigortalı teslimat ücretsiz")
        self._grand_lbl.setText(f"₺ {total:,.2f}")

    # ── Validasyon & sipariş gönderimi ───────────────────────

    def _submit(self) -> None:
        self._error_lbl.setText("")

        if self._method == "card":
            err = self._validate_card()
            if err:
                self._error_lbl.setText(f"⚠  {err}")
                return

        user = self._ctx.auth_service.get_current_user()
        if not user or not self._items:
            return

        # Kart kaydetme isteği — sipariş oluşturmadan önce yapalım ki
        # sipariş başarısız olursa kart yine de kayıt edilmiş olmasın
        if (self._method == "card"
                and self._selected_card is None
                and self._save_card_cb.isChecked()):
            try:
                mm, yy = self._card_expiry.text().strip().split("/")
                self._ctx.saved_card_service.save_card(
                    user_id=user.id,
                    holder=self._card_holder.text(),
                    card_number=self._card_number.text(),
                    expiry_mm=int(mm),
                    expiry_yy=int(yy),
                    title=self._save_title_input.text() or None,
                )
            except Exception as e:
                # Kayıt başarısız olsa bile siparişe devam ediyoruz
                Toast.show_error(self, f"Kart kaydedilemedi: {e}")

        rates = self._ctx.exchange_service.get_rates()
        gold  = rates.gold_gram_try if rates else 0.0
        cart_payload = [
            {"product_id": it["product"].id, "quantity": it["quantity"]}
            for it in self._items
        ]

        notes = None
        if self._method == "pickup":
            notes = f"Teslim Mağaza: {self._pickup_cb.currentText()}"

        try:
            order = self._ctx.order_service.create_order(
                user.id, cart_payload, gold,
                notes=notes,
                payment_method=self._method,
            )
            self._ctx.cart_service.clear_cart(user.id)
            self.order_completed.emit(order)
        except Exception as e:
            self._error_lbl.setText(f"⚠  Sipariş oluşturulamadı: {e}")
            Toast.show_error(self, "Sipariş oluşturulamadı")

    def _validate_card(self) -> str:
        cvv = self._card_cvv.text().strip()

        # Kayıtlı kart seçili → sadece CVV doğrula
        if self._selected_card is not None:
            if not re.fullmatch(r"\d{3,4}", cvv):
                return "CVV 3 hane olmalıdır."
            # Süresi geçmiş mi (kayıttayken geçerliydi ama şimdi dolmuş olabilir)
            now = datetime.now()
            sc = self._selected_card
            if (2000 + sc.expiry_yy, sc.expiry_mm) < (now.year, now.month):
                return "Seçili kartın son kullanma tarihi geçmiş — başka kart seçin."
            return ""

        # Yeni kart — tüm alanlar
        holder = self._card_holder.text().strip()
        number = re.sub(r"\D", "", self._card_number.text())
        expiry = self._card_expiry.text().strip()

        if not holder:
            return "Kart üzerindeki ismi giriniz."
        if len(number) != 16:
            return "Kart numarası 16 hane olmalıdır."
        if not re.fullmatch(r"\d{2}/\d{2}", expiry):
            return "Son kullanma tarihi AA/YY formatında olmalıdır."
        mm, yy = expiry.split("/")
        if not (1 <= int(mm) <= 12):
            return "Geçersiz ay."
        # Tarih geçmişte olmasın (yaklaşık kontrol)
        now = datetime.now()
        exp_year  = 2000 + int(yy)
        exp_month = int(mm)
        if (exp_year, exp_month) < (now.year, now.month):
            return "Kartın son kullanma tarihi geçmiş."
        if not re.fullmatch(r"\d{3}", cvv):
            return "CVV 3 hane olmalıdır."
        return ""

    # ── Kayıtlı kart yönetimi ────────────────────────────────

    def _reload_saved_cards(self) -> None:
        user = self._ctx.auth_service.get_current_user()
        if not user:
            self._saved_cards = []
        else:
            self._saved_cards = self._ctx.saved_card_service.list_for_user(user.id)
        self._render_card_strip()

        # Varsayılan kart varsa onu otomatik seç; yoksa "yeni kart" modunda kal
        default = next((c for c in self._saved_cards if c.is_default), None)
        if default:
            self._select_saved_card(default)
        else:
            self._select_new_card()

    def _render_card_strip(self) -> None:
        # Mevcut butonları temizle
        while self._cards_strip_lay.count():
            item = self._cards_strip_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._card_buttons.clear()

        # Kayıtlı kartlar
        for card in self._saved_cards:
            btn = self._build_card_chip(card)
            self._cards_strip_lay.addWidget(btn)
            self._card_buttons.append(btn)

        # "+ Yeni Kart" butonu her zaman var — tek satır, ortalı
        new_btn = QPushButton("＋  Yeni Kart")
        new_btn.setCheckable(True)
        new_btn.setFixedSize(140, 96)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setStyleSheet(self._chip_style(False, is_new=True))
        new_btn.clicked.connect(self._select_new_card)
        self._cards_strip_lay.addWidget(new_btn)
        self._card_buttons.append(new_btn)
        self._new_card_btn = new_btn

        # Hiç kayıtlı kart yoksa şeridi gizle (sadece "Yeni Kart" çıplak görünmesin)
        self._cards_section.setVisible(bool(self._saved_cards) or False)
        # Yine de yeni kart butonunu göstermek için açık tutalım — kullanıcı her zaman görsün
        self._cards_section.setVisible(True)

    def _build_card_chip(self, card: SavedCard) -> QPushButton:
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setFixedSize(190, 96)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Çok uzun başlığı kısalt
        title = card.display_title()
        if len(title) > 18:
            title = title[:17] + "…"
        last4 = f"•••• {card.last4}"
        meta  = f"Son Kul. {card.expiry_text()}"
        prefix = "★  " if card.is_default else f"{card.brand_icon()}  "
        text  = f"{prefix}{title}\n{last4}\n{meta}"
        btn.setText(text)
        btn.setStyleSheet(self._chip_style(False))
        btn.clicked.connect(lambda _=False, c=card: self._select_saved_card(c))
        return btn

    def _chip_style(self, active: bool, is_new: bool = False) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: {Colors.GOLD_SUBTLE};
                    color: {Colors.TEXT_H1};
                    border: 2px solid {Colors.GOLD};
                    border-radius: {Radius.MD};
                    text-align: left; padding: 10px 12px;
                    font-size: 11px; font-weight: 600;
                    font-family: {Fonts.FAMILY};
                }}
            """
        if is_new:
            return f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.GOLD};
                    border: 1px dashed {Colors.GOLD}88;
                    border-radius: {Radius.MD};
                    font-size: 11px; font-weight: 700;
                    font-family: {Fonts.FAMILY};
                }}
                QPushButton:hover {{
                    background: {Colors.GOLD_SUBTLE};
                    border-style: solid;
                }}
            """
        return f"""
            QPushButton {{
                background: {Colors.BG_RAISED};
                color: {Colors.TEXT_BODY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD};
                text-align: left; padding: 10px 12px;
                font-size: 11px;
                font-family: {Fonts.FAMILY};
            }}
            QPushButton:hover {{
                border-color: {Colors.GOLD}; color: {Colors.TEXT_H1};
            }}
        """

    def _select_saved_card(self, card: SavedCard) -> None:
        self._selected_card = card
        # Tüm chip butonlarını deaktive et
        for btn in self._card_buttons:
            btn.setChecked(False)
            is_new = (btn is getattr(self, "_new_card_btn", None))
            btn.setStyleSheet(self._chip_style(False, is_new=is_new))
        # Seçilen kartın butonunu aktive et — _card_buttons sıralaması:
        # [saved_cards..., new_card_btn]
        for i, c in enumerate(self._saved_cards):
            if c.id == card.id and i < len(self._card_buttons):
                self._card_buttons[i].setChecked(True)
                self._card_buttons[i].setStyleSheet(self._chip_style(True))
                break

        # Form alanlarını gizle — yalnızca CVV grubu görünür
        for w in (self._holder_group, self._number_group, self._expiry_group):
            w.hide()
        self._save_card_cb.hide()
        self._save_title_input.hide()
        self._cvv_group.show()

        # Seçili kart özetini göster
        self._selected_card_lbl.setText(
            f"Seçili kart: <b>{card.display_title()}</b>  ·  "
            f"{card.masked_number()}  ·  {card.expiry_text()}<br>"
            f"<span style='color:{Colors.TEXT_MUTED};font-size:11px;'>"
            f"Sahibi: {card.holder} — güvenlik için CVV'yi tekrar giriniz."
            f"</span>"
        )
        self._selected_card_lbl.show()
        self._card_cvv.clear()
        self._card_cvv.setFocus()
        self._error_lbl.setText("")

    def _select_new_card(self) -> None:
        self._selected_card = None
        # Buton durumlarını sıfırla, "Yeni Kart" aktif
        for btn in self._card_buttons:
            btn.setChecked(False)
            is_new = (btn is getattr(self, "_new_card_btn", None))
            btn.setStyleSheet(self._chip_style(is_new, is_new=is_new))
            if is_new:
                btn.setChecked(True)

        # Form alanlarını göster
        for w in (self._holder_group, self._number_group,
                  self._expiry_group, self._cvv_group):
            w.show()
        self._save_card_cb.show()
        self._save_title_input.show()
        self._selected_card_lbl.hide()
        self._error_lbl.setText("")

    def _open_cards_manager(self) -> None:
        dlg = SavedCardsDialog(self._ctx, parent=self)
        dlg.cards_changed.connect(self._reload_saved_cards)
        dlg.exec()
        # Kullanıcı dialog'da değişiklik yapmış olabilir — yeniden yükle
        self._reload_saved_cards()

    # ── Yardımcılar ──────────────────────────────────────────

    def _line_edit(self, placeholder: str) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setFixedHeight(40)
        le.setStyleSheet(input_field())
        return le
