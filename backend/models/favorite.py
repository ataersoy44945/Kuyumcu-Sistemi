from dataclasses import dataclass
from typing import Optional


@dataclass
class Favorite:
    """Kullanıcı-ürün favori ilişkisi."""

    user_id:    int
    product_id: int

    id:         Optional[int] = None
    created_at: str           = ""
