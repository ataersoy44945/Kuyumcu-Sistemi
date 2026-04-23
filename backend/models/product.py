from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Kuyumcu ürününü temsil eder. Fiyat hesaplama için gerekli tüm alanlar burada."""

    name:        str
    category_id: int
    weight_grams: float
    karat:       str          # "8" | "14" | "18" | "21" | "22" | "24"
    karat_coefficient: float  # karat/24 oranı, config.KARAT_COEFFICIENTS'dan atanır

    id:                   Optional[int]   = None
    description:          Optional[str]   = None
    labor_cost:           float           = 0.0
    profit_margin:        float           = 15.0
    base_price:           Optional[float] = None
    use_calculated_price: bool            = True
    stock_quantity:       int             = 0
    image_path:           Optional[str]   = None
    is_for_sale:          bool            = True
    favorite_count:       int             = 0
    created_by:           Optional[int]   = None
    created_at:           str             = ""
    updated_at:           str             = ""

    # DB JOIN ile gelen ek alan
    category_name: Optional[str] = None

    # ── Derived ────────────────────────────────────────────────

    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    def is_low_stock(self, threshold: int = 3) -> bool:
        return 0 < self.stock_quantity <= threshold

    def karat_label(self) -> str:
        return f"{self.karat} Ayar"
