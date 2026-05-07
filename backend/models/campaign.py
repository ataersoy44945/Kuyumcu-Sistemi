"""
Campaign modeli — kampanya dönemi boyunca aktif kalan indirim/promosyon tanımı.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Campaign:
    title:          str
    discount_type:  str           # 'percentage' | 'fixed' | 'shipping'
    discount_value: float
    start_date:     str           # "YYYY-MM-DD"
    end_date:       str           # "YYYY-MM-DD"

    id:          Optional[int] = None
    description: Optional[str] = None
    category:    Optional[str] = None   # "Yüzük, Kolye" veya "Tümü"
    badge:       Optional[str] = None
    image_path:  Optional[str] = None
    is_active:   bool          = True
    created_at:  str           = ""

    # ── Derived ──────────────────────────────────────────────

    def _parse_date(self, text: str) -> Optional[datetime]:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now()
        end = self._parse_date(self.end_date)
        return end is not None and now > end

    def time_remaining(self, now: Optional[datetime] = None) -> Optional[tuple[int, int, int]]:
        """Kalan süreyi (gün, saat, dakika) olarak döner; biten kampanyada None."""
        now = now or datetime.now()
        end = self._parse_date(self.end_date)
        if end is None or now > end:
            return None
        delta = end - now
        days    = delta.days
        hours   = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return days, hours, minutes

    def discount_label(self) -> str:
        """İndirim türüne göre insan-okunur etiket."""
        if self.discount_type == "percentage":
            return f"%{self.discount_value:g} İNDİRİM"
        if self.discount_type == "fixed":
            return f"₺{self.discount_value:,.0f} İNDİRİM"
        if self.discount_type == "shipping":
            return "ÜCRETSİZ KARGO"
        return ""

    def categories_list(self) -> list[str]:
        """category alanını liste olarak döner."""
        if not self.category or self.category.strip().lower() in ("tümü", "tumu", "all"):
            return []
        return [c.strip() for c in self.category.split(",") if c.strip()]
