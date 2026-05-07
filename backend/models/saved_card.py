"""
Kayıtlı (tokenize edilmemiş) kart bilgisi.

PCI-DSS uyumu açısından üretimde gerçek kart numarası ASLA saklanmamalıdır.
Bu deneme sisteminde sadece görüntüleme amaçlı parçalar tutulur:
    - Kart sahibi
    - BIN (ilk 6 hane) — marka / banka tespiti için
    - Son 4 hane — UI'de "•••• 4242"
    - Marka (visa / mastercard / amex / troy / unknown)
    - Son kullanma ay/yıl
CVV ve tam PAN HER ZAMAN dışarıda — ödeme anında her seferinde sorulur.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SavedCard:
    user_id:    int
    holder:     str
    bin:        str         # ilk 6 hane
    last4:      str         # son 4 hane
    expiry_mm:  int
    expiry_yy:  int

    id:         Optional[int] = None
    title:      Optional[str] = None
    brand:      str           = "unknown"   # visa | mastercard | amex | troy | unknown
    is_default: bool          = False
    created_at: str           = ""

    # ── Sunum yardımcıları ───────────────────────────────────

    def masked_number(self) -> str:
        """•••• •••• •••• 4242 görünümü."""
        return f"•••• •••• •••• {self.last4}"

    def expiry_text(self) -> str:
        return f"{self.expiry_mm:02d}/{self.expiry_yy:02d}"

    def display_title(self) -> str:
        """Kullanıcının verdiği isim yoksa marka + son 4 hane."""
        if self.title:
            return self.title
        return f"{self.brand_label()} •••• {self.last4}"

    def brand_label(self) -> str:
        return {
            "visa":       "Visa",
            "mastercard": "Mastercard",
            "amex":       "American Express",
            "troy":       "Troy",
            "unknown":    "Kart",
        }.get(self.brand, "Kart")

    def brand_icon(self) -> str:
        return {
            "visa":       "🅥",
            "mastercard": "🅼",
            "amex":       "🅰",
            "troy":       "🅣",
        }.get(self.brand, "💳")


def detect_brand(card_number: str) -> str:
    """Kart numarasından marka tespiti — sadece BIN'e bakar."""
    n = "".join(ch for ch in card_number if ch.isdigit())
    if not n:
        return "unknown"

    # American Express: 34, 37
    if n.startswith(("34", "37")):
        return "amex"
    # Visa: 4
    if n.startswith("4"):
        return "visa"
    # Mastercard: 51-55 ya da 2221-2720
    if len(n) >= 2 and n[:2] in ("51", "52", "53", "54", "55"):
        return "mastercard"
    if len(n) >= 4:
        try:
            prefix4 = int(n[:4])
            if 2221 <= prefix4 <= 2720:
                return "mastercard"
        except ValueError:
            pass
    # Troy: 9792 ya da bazı 65xx aralıkları
    if n.startswith("9792"):
        return "troy"
    if len(n) >= 4 and n[:4] in ("6501", "6502", "6503", "6504"):
        return "troy"

    return "unknown"
