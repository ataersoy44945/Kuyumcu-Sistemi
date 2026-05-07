"""
Frontend yardımcıları — tekrar eden küçük işlevler.
"""

from typing import Optional


# ── Kategori ikon haritası ────────────────────────────────────
# Sıra önemli: daha spesifik isimler (örn. "bileklik") "bilezik"ten
# önce eşleşmeli.
def category_icon(name: str) -> str:
    """Kategori adına göre uygun emoji ikonu döner."""
    n = (name or "").lower().strip()
    if "bileklik" in n:            return "🔗"
    if "bilezik"  in n:            return "🟡"
    if "yüzük"    in n:            return "💍"
    if "kolye"    in n:            return "📿"
    if "küpe"     in n:            return "👂"
    if "zincir"   in n:            return "⛓"
    if "set"      in n:            return "💎"
    if "erkek"    in n:            return "🧔"
    if "çocuk"    in n:            return "👶"
    if "özel"     in n:            return "✨"
    if "altın"    in n:            return "🪙"
    if "koleksiyon" in n:          return "🏆"
    return "🏷"


# ── Ürün alt-kategori çıkarma ─────────────────────────────────
# Seed script'i "Alt: X · ..." formatında description'a gömdü.

def product_subcategory(product) -> Optional[str]:
    """Product description'dan 'Alt: X' değerini çıkarır. Yoksa None."""
    desc = getattr(product, "description", None) or ""
    if "Alt:" not in desc:
        return None

    after = desc.split("Alt:", 1)[1]
    # İlk satıra sınırla
    after = after.split("\n", 1)[0]
    # "·" veya "|" gibi ayraçlarda kes
    for sep in ("·", "|"):
        if sep in after:
            after = after.split(sep, 1)[0]
            break
    value = after.strip()
    return value or None
