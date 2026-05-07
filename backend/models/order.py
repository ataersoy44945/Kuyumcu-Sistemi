from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrderItem:
    """Bir siparişe ait tek ürün satırı."""

    order_id:           int
    product_id:         int
    quantity:           int
    unit_price:         float

    id:                  Optional[int]   = None
    gold_rate_at_order:  Optional[float] = None
    created_at:          str             = ""

    # JOIN ile gelen ek alanlar
    product_name: Optional[str] = None


@dataclass
class Order:
    """Müşteri sipariş başlığı."""

    user_id:      int
    total_amount: float

    id:              Optional[int] = None
    status:          str           = "pending"   # pending | processing | completed | cancelled
    shipping_amount: float         = 0.0
    payment_method:  Optional[str] = None        # card | transfer | cod | pickup
    order_number:    Optional[str] = None        # KJ-2026-48392
    notes:           Optional[str] = None
    admin_notes:     Optional[str] = None
    created_at:      str           = ""
    updated_at:      str           = ""

    items: list[OrderItem] = field(default_factory=list)

    # JOIN ile gelen ek alanlar
    user_full_name: Optional[str] = None

    def subtotal(self) -> float:
        """Ürün ara toplamı (kargo hariç)."""
        return round(max(0.0, self.total_amount - (self.shipping_amount or 0.0)), 2)

    def status_label(self) -> str:
        # status + payment_method'a göre kullanıcıya gösterilecek etiket.
        # "Ödeme Bekleniyor" yalnızca havale/EFT pending sipariş için anlamlı.
        if self.status == "pending" and self.payment_method == "transfer":
            return "Ödeme Bekleniyor"
        labels = {
            "pending":    "Hazırlanıyor",
            "processing": "Onaylandı",
            "completed":  "Teslim Edildi",
            "cancelled":  "İptal",
        }
        return labels.get(self.status, self.status)

    def payment_method_label(self) -> str:
        return {
            "card":     "Kredi / Banka Kartı",
            "transfer": "Havale / EFT",
            "cod":      "Kapıda Ödeme",
            "pickup":   "Mağazadan Teslim",
        }.get(self.payment_method or "", "—")
