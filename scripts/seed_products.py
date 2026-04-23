"""
50 örnek ürünü veritabanına ekler.
- Gerekli kategorileri otomatik oluşturur.
- product_code, subcategory, featured, campaign bilgileri description'a gömülür.
- extra_profit → profit_margin % olarak çevrilir (referans gram altın = 2400 TL).
- pricing_type=otomatik → use_calculated_price=True
"""

import sys
from pathlib import Path

# Proje kökünü sys.path'e ekle
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config
from backend.app_context import AppContext


# ── Referans gram altın fiyatı (margin% hesabı için) ─────────
REF_GOLD_GRAM = 2400.0

KARAT_COEF = {
    "8":  8 / 24,
    "14": 14 / 24,
    "18": 18 / 24,
    "21": 21 / 24,
    "22": 22 / 24,
    "24": 1.0,
}


# ── Ham ürün verisi ──────────────────────────────────────────
# Her satır: (name, code, category, subcategory, karat, gram,
#            labor, extra_profit, stock, description, featured, campaign, image)

PRODUCTS = [
    ("Tektaş Yüzük",           "YZK-2026-001", "Yüzük",             "Taşlı",        "14", 2.85,  1750, 900,  8,  "Zarif taş detaylı, günlük ve özel gün kullanımı için uygun modern tektaş yüzük.",                             True,  False, "assets/products/yzk_001.jpg"),
    ("Klasik Alyans",          "YZK-2026-002", "Yüzük",             "Sade",         "22", 4.10,  1400, 850,  12, "Düz ve klasik tasarıma sahip, evlilik ve nişan için tercih edilen sade alyans modelidir.",                     False, False, "assets/products/yzk_002.jpg"),
    ("Baget Taşlı Yüzük",      "YZK-2026-003", "Yüzük",             "Modern",       "14", 3.20,  2100, 1100, 6,  "Baget kesim taş detaylarıyla dikkat çeken şık ve gösterişli yüzük modeli.",                                    True,  True,  "assets/products/yzk_003.jpg"),
    ("Minimal Yüzük",          "YZK-2026-004", "Yüzük",             "Minimal",      "8",  1.95,  900,  450,  14, "Günlük kullanım için hafif ve modern çizgilere sahip minimal yüzük.",                                          False, False, "assets/products/yzk_004.jpg"),
    ("Vintage Yüzük",          "YZK-2026-005", "Yüzük",             "Vintage",      "14", 3.75,  1950, 1000, 5,  "Klasik motiflerle hazırlanmış dikkat çekici vintage yüzük modeli.",                                            True,  False, "assets/products/yzk_005.jpg"),

    ("Altın Damla Kolye",      "KLY-2026-001", "Kolye",             "Zarif",        "14", 5.10,  2200, 1000, 7,  "Damla formunda taş detaylı, günlük şıklık sunan ince zincirli altın kolye.",                                   True,  False, "assets/products/kly_001.jpg"),
    ("Kalp Motifli Kolye",     "KLY-2026-002", "Kolye",             "Romantik",     "14", 4.40,  1700, 850,  9,  "Kalp figürü ile duygusal ve zarif bir görünüm sunan ince işçilikli kolye.",                                    False, True,  "assets/products/kly_002.jpg"),
    ("Kişiye Özel Harf Kolye", "KLY-2026-003", "Kolye",             "Kişisel",      "8",  3.10,  1500, 700,  10, "Harf detaylı, kişisel kullanım ve hediye için ideal minimal altın kolye.",                                      False, False, "assets/products/kly_003.jpg"),
    ("Yonca Kolye",            "KLY-2026-004", "Kolye",             "Şans",         "14", 4.85,  1800, 900,  8,  "Yonca figürlü şık kolye, modern ve zarif kombinler için uygundur.",                                            True,  False, "assets/products/kly_004.jpg"),
    ("Güneş Kolye",            "KLY-2026-005", "Kolye",             "Modern",       "14", 5.25,  2100, 950,  6,  "Parlak yüzeyi ve güneş formu ile dikkat çeken premium kolye modeli.",                                          True,  True,  "assets/products/kly_005.jpg"),

    ("Halka Küpe",             "KUP-2026-001", "Küpe",              "Klasik",       "14", 3.20,  1300, 800,  15, "Günlük kullanım için uygun, taş detaylı şık halka küpe modeli.",                                               True,  False, "assets/products/kup_001.jpg"),
    ("Sallantılı Taşlı Küpe",  "KUP-2026-002", "Küpe",              "Şık",          "14", 4.00,  1900, 950,  5,  "Özel davet ve şık kombinler için tasarlanmış sallantılı küpe modeli.",                                         True,  True,  "assets/products/kup_002.jpg"),
    ("Mini Günlük Küpe",       "KUP-2026-003", "Küpe",              "Minimal",      "8",  1.90,  850,  500,  14, "Hafif yapısı ile günlük kullanım için ideal, sade ve zarif mini küpe.",                                         False, False, "assets/products/kup_003.jpg"),
    ("İnci Detaylı Küpe",      "KUP-2026-004", "Küpe",              "Zarif",        "14", 3.60,  1650, 850,  7,  "İnci ve altın uyumu ile hazırlanmış klasik-şık küpe modeli.",                                                   False, True,  "assets/products/kup_004.jpg"),
    ("Kare Form Küpe",         "KUP-2026-005", "Küpe",              "Modern",       "14", 2.95,  1200, 700,  9,  "Geometrik tasarımıyla modern çizgileri sevenler için özel küpe modeli.",                                        False, False, "assets/products/kup_005.jpg"),

    ("22 Ayar Burma Bilezik",  "BLZ-2026-001", "Bilezik",           "Geleneksel",   "22", 20.15, 3200, 1800, 4,  "Geleneksel işçiliği modern görünümle birleştiren 22 ayar burma bilezik modeli.",                                True,  False, "assets/products/blz_001.jpg"),
    ("Kelepçe Bilezik",        "BLZ-2026-002", "Bilezik",           "Modern",       "14", 9.80,  2600, 1400, 6,  "Şık çizgilere sahip modern kelepçe bilezik, özel günler için premium seçimdir.",                               True,  True,  "assets/products/blz_002.jpg"),
    ("İnce Zarif Bilezik",     "BLZ-2026-003", "Bilezik",           "Zarif",        "14", 6.40,  1750, 950,  10, "Günlük kullanım için rahat ve hafif, ince formda zarif bilezik modeli.",                                        False, False, "assets/products/blz_003.jpg"),
    ("Taşlı Kelepçe Bilezik",  "BLZ-2026-004", "Bilezik",           "Taşlı",        "14", 8.75,  2400, 1300, 5,  "Taş süslemeleri ile premium görünüm sunan özel tasarım kelepçe bilezik.",                                      True,  False, "assets/products/blz_004.jpg"),
    ("Burgu Bilezik",          "BLZ-2026-005", "Bilezik",           "Klasik",       "22", 15.30, 2800, 1550, 4,  "Klasik burgu formu ile geleneksel altın bilezik görünümünü taşır.",                                             False, True,  "assets/products/blz_005.jpg"),

    ("İnce Altın Zincir",      "ZNC-2026-001", "Zincir",            "Minimal",      "14", 4.70,  1500, 800,  11, "Kolye uçlarıyla uyumlu kullanılabilen sade ve ince altın zincir modeli.",                                      False, False, "assets/products/znc_001.jpg"),
    ("Kalın Altın Zincir",     "ZNC-2026-002", "Zincir",            "Gösterişli",   "22", 12.60, 2900, 1600, 5,  "Daha dikkat çekici ve güçlü görünüm isteyen kullanıcılar için kalın zincir modelidir.",                         True,  False, "assets/products/znc_002.jpg"),
    ("İtalyan Zincir",         "ZNC-2026-003", "Zincir",            "Premium",      "14", 7.40,  2300, 1200, 6,  "İnce işçiliğe sahip premium görünümlü İtalyan tarzı zincir.",                                                   True,  True,  "assets/products/znc_003.jpg"),
    ("Burgu Zincir",           "ZNC-2026-004", "Zincir",            "Klasik",       "14", 6.20,  1850, 950,  7,  "Klasik zincir yapısına göre daha gösterişli, hafif burgu desenli model.",                                       False, False, "assets/products/znc_004.jpg"),
    ("Kalp Uçlu Zincir",       "ZNC-2026-005", "Zincir",            "Romantik",     "8",  3.80,  1250, 650,  8,  "Kalp uç detaylı, zarif ve hediye amaçlı tercih edilen zincir modeli.",                                          False, True,  "assets/products/znc_005.jpg"),

    ("Zarif Takı Seti",        "SET-2026-001", "Set",               "Şık",          "14", 14.20, 4200, 2200, 3,  "Kolye, küpe ve yüzük uyumundan oluşan özel günlere uygun premium takı seti.",                                   True,  True,  "assets/products/set_001.jpg"),
    ("Gelin Takı Seti",        "SET-2026-002", "Set",               "Özel Gün",     "22", 24.50, 5500, 3000, 2,  "Düğün ve nişan organizasyonları için hazırlanmış gösterişli ve ağır işçilikli set.",                             True,  False, "assets/products/set_002.jpg"),
    ("Minimal Takı Seti",      "SET-2026-003", "Set",               "Minimal",      "8",  9.60,  2600, 1300, 4,  "Günlük kullanım için tasarlanmış sade ve hafif parçalardan oluşan set.",                                        False, False, "assets/products/set_003.jpg"),
    ("Taşlı Davet Seti",       "SET-2026-004", "Set",               "Davet",        "14", 16.80, 4600, 2400, 2,  "Özel geceler ve davetler için dikkat çekici tasarlanmış takı seti.",                                            True,  True,  "assets/products/set_004.jpg"),
    ("Klasik Set",             "SET-2026-005", "Set",               "Geleneksel",   "22", 18.90, 5000, 2600, 2,  "Klasik altın severler için hazırlanan ağır işçilikli geleneksel set.",                                           False, False, "assets/products/set_005.jpg"),

    ("Çeyrek Altın",           "ALT-2026-001", "Çeyrek Altın",      "Yatırımlık",   "22", 1.75,  150,  120,  20, "Yatırım ve hediye amaçlı tercih edilen klasik çeyrek altın.",                                                   True,  False, "assets/products/alt_001.jpg"),
    ("Yarım Altın",            "ALT-2026-002", "Yarım Altın",       "Yatırımlık",   "22", 3.50,  180,  150,  15, "Çeyrek altına göre daha yüksek değerli, yatırımlık yarım altın ürünü.",                                          False, False, "assets/products/alt_002.jpg"),
    ("Tam Altın",              "ALT-2026-003", "Tam Altın",         "Yatırımlık",   "22", 7.00,  250,  180,  10, "Geleneksel ve yatırım amaçlı kullanılan tam altın modeli.",                                                     True,  False, "assets/products/alt_003.jpg"),
    ("Ata Altın",              "ALT-2026-004", "Ata Altın",         "Yatırımlık",   "22", 7.20,  280,  200,  9,  "Yatırım amaçlı tercih edilen güçlü değere sahip ata altın modeli.",                                              True,  False, "assets/products/alt_004.jpg"),
    ("Ziynet Altın",           "ALT-2026-005", "Ziynet Altın",      "Hediyelik",    "22", 7.10,  240,  170,  8,  "Hem yatırım hem hediye amaçlı alınabilen ziynet altın ürünü.",                                                   False, True,  "assets/products/alt_005.jpg"),

    ("Altın Bileklik",         "BLK-2026-001", "Bileklik",          "Günlük",       "14", 5.60,  1650, 850,  8,  "Hafif ve zarif tasarımıyla günlük kullanım için uygun altın bileklik modeli.",                                  False, True,  "assets/products/blk_001.jpg"),
    ("Taşlı Altın Bileklik",   "BLK-2026-002", "Bileklik",          "Taşlı",        "14", 6.10,  2100, 1000, 6,  "Parlak taş detaylarıyla premium görünüm sunan altın bileklik.",                                                 True,  False, "assets/products/blk_002.jpg"),
    ("İnce Zincir Bileklik",   "BLK-2026-003", "Bileklik",          "Minimal",      "8",  3.25,  1100, 550,  11, "Günlük ve hafif kullanıma uygun ince zincir formunda bileklik.",                                                False, False, "assets/products/blk_003.jpg"),
    ("Yonca Bileklik",         "BLK-2026-004", "Bileklik",          "Modern",       "14", 4.95,  1750, 900,  7,  "Yonca motifli, sade ama şık detaylara sahip modern bileklik.",                                                   False, True,  "assets/products/blk_004.jpg"),
    ("Kalp Detaylı Bileklik",  "BLK-2026-005", "Bileklik",          "Romantik",     "14", 4.55,  1600, 800,  9,  "Kalp detayları ile zarif görünüm sunan hediye amaçlı bileklik modeli.",                                          False, False, "assets/products/blk_005.jpg"),

    ("Çocuk Küpe",             "CCK-2026-001", "Çocuk Takıları",    "Küpe",         "8",  1.20,  650,  300,  12, "Hafif yapılı, çocuk kullanımına uygun sevimli altın küpe modeli.",                                              False, True,  "assets/products/cck_001.jpg"),
    ("Çocuk Bileklik",         "CCK-2026-002", "Çocuk Takıları",    "Bileklik",     "8",  2.40,  900,  400,  10, "Çocuklar için tasarlanmış hafif ve zarif altın bileklik modeli.",                                                False, False, "assets/products/cck_002.jpg"),
    ("Çocuk Kolye",            "CCK-2026-003", "Çocuk Takıları",    "Kolye",        "8",  2.10,  850,  350,  9,  "Küçük figür detaylı, çocuklara uygun altın kolye modeli.",                                                       False, True,  "assets/products/cck_003.jpg"),

    ("Nazar Boncuklu Kolye",   "OZG-2026-001", "Özel Tasarım",      "Nazar",        "14", 4.30,  1700, 850,  6,  "Nazar boncuğu detaylarıyla hazırlanmış modern ve anlamlı kolye modeli.",                                        True,  False, "assets/products/ozg_001.jpg"),
    ("Melek Kanadı Kolye",     "OZG-2026-002", "Özel Tasarım",      "Simgesel",     "14", 4.95,  1850, 900,  5,  "Melek kanadı formuyla özel anlam taşıyan zarif kolye tasarımı.",                                                 True,  True,  "assets/products/ozg_002.jpg"),
    ("Sonsuzluk Bileklik",     "OZG-2026-003", "Özel Tasarım",      "Sonsuzluk",    "14", 3.85,  1500, 750,  8,  "Sonsuzluk figürüyle duygusal anlam taşıyan ince bileklik modeli.",                                               False, False, "assets/products/ozg_003.jpg"),
    ("Harf Yüzük",             "OZG-2026-004", "Özel Tasarım",      "Kişisel",      "8",  2.35,  1150, 600,  7,  "Harf motifli, kişiselleştirmeye uygun modern yüzük modeli.",                                                    False, True,  "assets/products/ozg_004.jpg"),
    ("Taç Yüzük",              "OZG-2026-005", "Özel Tasarım",      "Prenses",      "14", 3.40,  1900, 1000, 5,  "Taç formundaki gösterişli tasarımıyla dikkat çeken özel yüzük modeli.",                                          True,  False, "assets/products/ozg_005.jpg"),

    ("Erkek Zincir Bileklik",  "ERK-2026-001", "Erkek Koleksiyonu", "Bileklik",     "14", 7.80,  2400, 1200, 6,  "Daha maskülen çizgiler taşıyan güçlü görünümlü erkek bileklik modeli.",                                          True,  False, "assets/products/erk_001.jpg"),
    ("Erkek Kalın Zincir",     "ERK-2026-002", "Erkek Koleksiyonu", "Zincir",       "22", 13.40, 3100, 1750, 4,  "Erkek koleksiyonuna özel, güçlü ve premium görünüm sunan kalın zincir modeli.",                                  True,  True,  "assets/products/erk_002.jpg"),
]


def _margin_pct(gram: float, karat: str, extra_profit: float) -> float:
    """extra_profit'i referans altın fiyatı ile margin % olarak döndürür."""
    coef = KARAT_COEF[karat]
    gold_value = gram * REF_GOLD_GRAM * coef
    if gold_value <= 0:
        return 15.0
    pct = (extra_profit / gold_value) * 100
    return max(0.1, min(99.9, round(pct, 2)))


def _build_description(code: str, subcategory: str, featured: bool,
                        campaign: bool, desc: str) -> str:
    tags = [f"[KOD: {code}]", f"Alt: {subcategory}"]
    if featured:
        tags.append("★ ÖNE ÇIKAN")
    if campaign:
        tags.append("🎯 KAMPANYA")
    return "  ·  ".join(tags) + "\n" + desc


def main() -> None:
    ctx = AppContext(db_path=config.DB_PATH)

    # Admin kullanıcıyı bul (created_by için)
    admin_row = ctx.db.get_connection().execute(
        "SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1"
    ).fetchone()
    admin_id = admin_row["id"] if admin_row else 1

    # Mevcut kategorileri map'le, eksikleri ekle
    cat_map: dict[str, int] = {
        c.name: c.id for c in ctx.product_service.get_categories(active_only=False)
    }

    needed = {p[2] for p in PRODUCTS}
    for name in needed:
        if name not in cat_map:
            try:
                created = ctx.product_service.add_category(name)
                cat_map[name] = created.id
                print(f"  [+kategori] {name} (id={created.id})")
            except ValueError:
                # Yarış koşulu — yeniden yükle
                cat_map = {c.name: c.id for c in ctx.product_service.get_categories(active_only=False)}

    # Duplicate kontrol için mevcut isimleri al
    existing = {p.name for p in ctx.product_service.get_all(for_sale_only=False)}

    added, skipped = 0, 0
    for row in PRODUCTS:
        (name, code, category, subcategory, karat, gram,
         labor, extra_profit, stock, desc, featured, campaign, image) = row

        if name in existing:
            print(f"  [~] {name} zaten var, atlandı")
            skipped += 1
            continue

        data = {
            "name": name,
            "category_id": cat_map[category],
            "weight_grams": gram,
            "karat": karat,
            "description": _build_description(code, subcategory, featured, campaign, desc),
            "labor_cost": labor,
            "profit_margin": _margin_pct(gram, karat, extra_profit),
            "use_calculated_price": True,
            "stock_quantity": stock,
            "image_path": image,
            "is_for_sale": True,
        }
        try:
            p = ctx.product_service.add_product(data, admin_id=admin_id)
            print(f"  [+] {p.name} (#{p.id}) — {category}")
            added += 1
        except Exception as e:
            print(f"  [!] {name} hata: {e}")

    ctx.shutdown()
    print(f"\nToplam: {added} eklendi, {skipped} atlandı.")


if __name__ == "__main__":
    main()
