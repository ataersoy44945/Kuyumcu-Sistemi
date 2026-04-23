"""
10 örnek kampanyayı veritabanına ekler.
- Tarihler bugünden başlar, her biri farklı bitiş süresiyle aktif tutulur.
- Görseller assets/campaigns/ klasörüne bağlıdır (yoksa kart fallback emoji gösterir).
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from backend.app_context import AppContext
from backend.models.campaign import Campaign


def _date(days_from_now: int) -> str:
    return (datetime.now() + timedelta(days=days_from_now)).strftime("%Y-%m-%d %H:%M:%S")


# Her satır: (title, desc, d_type, d_value, category, badge, image, days_duration)
CAMPAIGNS = [
    ("%10 İşçilik İndirimi",
     "Tüm bilezik modellerinde işçilik ücretine özel %10 indirim fırsatı.",
     "percentage", 10, "Bilezik", "Popüler",
     "assets/images/products/%10 İşçilik İndirimi.jpg", 45),

    ("Sevgililer Günü Kampanyası",
     "Kolye ve yüzüklerde çiftlere özel %15 indirim fırsatı.",
     "percentage", 15, "Yüzük, Kolye", "Yeni",
     "assets/images/products/Sevgililer Günü Kampanyası.jpg", 30),

    ("Ücretsiz Kargo",
     "2500 TL ve üzeri tüm alışverişlerde ücretsiz kargo fırsatı.",
     "shipping", 0, "Tümü", "Aktif",
     "assets/images/products/Ücretsiz Kargo.jpg", 120),

    ("Premium Set İndirimi",
     "Takı setlerinde sınırlı süreli %20 indirim fırsatı.",
     "percentage", 20, "Set", "Sınırlı",
     "assets/images/products/Premium Set İndirimi.jpg", 14),

    ("Yaz Koleksiyonu",
     "Yeni sezon yaz koleksiyonunda seçili ürünlerde %12 indirim.",
     "percentage", 12, "Koleksiyon", "Yeni",
     "assets/images/products/Yaz Koleksiyonu.jpg", 75),

    ("Altın Alışveriş Bonusu",
     "10.000 TL üzeri alışverişlerde 500 TL indirim.",
     "fixed", 500, "Tümü", "Popüler",
     "assets/images/products/Altın Alışveriş Bonusu.jpg", 60),

    ("Küpe Kampanyası",
     "Tüm küpe modellerinde ikinci ürüne %25 indirim fırsatı.",
     "percentage", 25, "Küpe", "Fırsat",
     "assets/images/products/Küpe Kampanyası.jpg", 21),

    ("Zincir Haftası",
     "Altın zincir modellerinde %8 indirim fırsatı.",
     "percentage", 8, "Zincir", "Kampanya",
     "assets/images/products/Zincir Haftası.jpg", 10),

    ("Erkek Koleksiyonu İndirimi",
     "Erkek koleksiyonundaki seçili ürünlerde %10 indirim.",
     "percentage", 10, "Erkek Koleksiyonu", "Yeni",
     "assets/images/products/Erkek Koleksiyonu.jpg", 40),

    ("Çocuk Takıları Kampanyası",
     "Çocuk takılarında sınırlı süreli %15 indirim fırsatı.",
     "percentage", 15, "Çocuk Takıları", "Fırsat",
     "assets/images/products/Çocuk Takıları Kampanyası.jpg", 30),
]


def main() -> None:
    ctx  = AppContext(db_path=config.DB_PATH)
    svc  = ctx.campaign_service

    existing = {c.title for c in svc.get_all()}

    added, skipped = 0, 0
    for title, desc, d_type, d_value, category, badge, image, days in CAMPAIGNS:
        if title in existing:
            print(f"  [~] {title} zaten var, atlandı")
            skipped += 1
            continue

        c = Campaign(
            title=title,
            description=desc,
            discount_type=d_type,
            discount_value=float(d_value),
            category=category,
            start_date=_date(0),
            end_date=_date(days),
            badge=badge,
            image_path=image,
            is_active=True,
        )
        created = svc.create(c)
        if created:
            print(f"  [+] {title}  ({badge})  — {days} gün aktif")
            added += 1
        else:
            print(f"  [!] {title} eklenemedi")

    ctx.shutdown()
    print(f"\nToplam: {added} eklendi, {skipped} atlandı.")


if __name__ == "__main__":
    main()
