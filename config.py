"""
Uygulama geneli yapılandırma.
Tüm sabitler, yollar ve ayarlar tek noktadan yönetilir.
"""

from pathlib import Path

# ── Dizinler ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent

DATA_DIR            = BASE_DIR / "data"
ASSETS_DIR          = BASE_DIR / "assets"
ICONS_DIR           = ASSETS_DIR / "icons"
IMAGES_DIR          = ASSETS_DIR / "images"
PRODUCT_IMAGES_DIR  = IMAGES_DIR / "products"
LOG_DIR             = BASE_DIR / "logs"

# Eksik dizinleri oluştur
for _d in (DATA_DIR, LOG_DIR, PRODUCT_IMAGES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Veritabanı ────────────────────────────────────────────────
DB_PATH = DATA_DIR / "app.db"

# ── Uygulama Bilgisi ──────────────────────────────────────────
APP_NAME    = "Kuyumcu Yönetim Sistemi"
APP_VERSION = "1.0.0"
WINDOW_MIN_W = 1200
WINDOW_MIN_H = 750

# ── Loglama ───────────────────────────────────────────────────
LOG_FILE  = LOG_DIR / "app.log"
LOG_LEVEL = "INFO"

# ── Kur Servisi ───────────────────────────────────────────────
EXCHANGE_RATE_CACHE_MINUTES = 15
EXCHANGE_RATE_TIMEOUT_SEC   = 8

# ── Fiyat Hesaplama ───────────────────────────────────────────
DEFAULT_PROFIT_MARGIN = 15.0   # yüzde

# Karat katsayıları: N/24 oranı saflık derecesini gösterir
KARAT_COEFFICIENTS: dict[str, float] = {
    "8":  round(8  / 24, 6),
    "14": round(14 / 24, 6),
    "18": round(18 / 24, 6),
    "21": round(21 / 24, 6),
    "22": round(22 / 24, 6),
    "24": round(24 / 24, 6),
}

# Altın çeşitlerine göre gram ağırlıkları (standart Türk altın birimleri)
GOLD_WEIGHTS: dict[str, float] = {
    "gram_altin":    1.00,
    "ceyrek_altin":  1.75,
    "yarim_altin":   3.50,
    "tam_altin":     7.00,
}

# ── Sayfalama ─────────────────────────────────────────────────
PRODUCTS_PER_PAGE = 20

# ── Stok Uyarı Eşiği ─────────────────────────────────────────
LOW_STOCK_THRESHOLD = 3

# ── Sipariş Durumları ─────────────────────────────────────────
ORDER_STATUSES = {
    "pending":    "Beklemede",
    "processing": "İşlemde",
    "completed":  "Tamamlandı",
    "cancelled":  "İptal",
}

# ── Kullanıcı Rolleri ─────────────────────────────────────────
ROLES = {
    "admin":    "Yönetici",
    "customer": "Müşteri",
}
