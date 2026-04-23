from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """Ürün kategorisi."""

    name: str

    id:            Optional[int] = None
    description:   Optional[str] = None
    icon_name:     Optional[str] = None
    display_order: int           = 0
    is_active:     bool          = True
    created_at:    str           = ""

    # İstatistik (JOIN ile gelebilir)
    product_count: int = 0
