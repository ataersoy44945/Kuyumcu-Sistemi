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

    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class Order:
    """Müşteri sipariş başlığı."""

    user_id:      int
    total_amount: float

    id:          Optional[int] = None
    status:      str           = "pending"   # pending | processing | completed | cancelled
    notes:       Optional[str] = None
    admin_notes: Optional[str] = None
    created_at:  str           = ""
    updated_at:  str           = ""

    items: list[OrderItem] = field(default_factory=list)

    # JOIN ile gelen ek alanlar
    user_full_name: Optional[str] = None

    def status_label(self) -> str:
        labels = {
            "pending":    "Beklemede",
            "processing": "İşlemde",
            "completed":  "Tamamlandı",
            "cancelled":  "İptal",
        }
        return labels.get(self.status, self.status)
