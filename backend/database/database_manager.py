"""
DatabaseManager — SQLite bağlantısı ve şema yönetimi.
Singleton pattern: uygulama boyunca tek bir bağlantı nesnesi yaşar.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Veritabanı bağlantısını ve şema oluşturmayı yönetir.
    Tablo tanımları, SQL sorguları ve migration'lar buraya aittir.
    Repository'ler bu sınıftan bağlantı alır — kendi bağlantılarını açmazlar.
    """

    _instance: "DatabaseManager | None" = None

    def __init__(self, db_path: Path):
        self._db_path   = db_path
        self._conn: sqlite3.Connection | None = None

    # ── Singleton Arayüzü ─────────────────────────────────────

    @classmethod
    def initialize(cls, db_path: Path) -> "DatabaseManager":
        """İlk çağrıda bağlantıyı açar ve şemayı oluşturur."""
        if cls._instance is None:
            cls._instance = cls(db_path)
            cls._instance._connect()
            cls._instance._create_schema()
            cls._instance._seed_defaults()
            logger.info("Veritabanı başlatıldı: %s", db_path)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            raise RuntimeError("DatabaseManager.initialize() önce çağrılmalıdır.")
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            DatabaseManager._instance = None
            logger.info("Veritabanı bağlantısı kapatıldı.")

    # ── Private ───────────────────────────────────────────────

    def _connect(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")

    def _create_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                email         TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'customer'
                                      CHECK(role IN ('admin', 'customer')),
                first_name    TEXT    NOT NULL,
                last_name     TEXT    NOT NULL,
                phone         TEXT,
                is_active     INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                last_login_at TEXT
            );

            CREATE TABLE IF NOT EXISTS categories (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL UNIQUE,
                description   TEXT,
                icon_name     TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                is_active     INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id          INTEGER NOT NULL,
                name                 TEXT    NOT NULL,
                description          TEXT,
                weight_grams         REAL    NOT NULL CHECK(weight_grams > 0),
                karat                TEXT    NOT NULL CHECK(karat IN ('8','14','18','21','22','24')),
                karat_coefficient    REAL    NOT NULL CHECK(karat_coefficient > 0 AND karat_coefficient <= 1),
                labor_cost           REAL    NOT NULL DEFAULT 0  CHECK(labor_cost >= 0),
                profit_margin        REAL    NOT NULL DEFAULT 15 CHECK(profit_margin >= 0 AND profit_margin <= 100),
                base_price           REAL             CHECK(base_price IS NULL OR base_price >= 0),
                use_calculated_price INTEGER NOT NULL DEFAULT 1  CHECK(use_calculated_price IN (0,1)),
                stock_quantity       INTEGER NOT NULL DEFAULT 0  CHECK(stock_quantity >= 0),
                image_path           TEXT,
                is_for_sale          INTEGER NOT NULL DEFAULT 1  CHECK(is_for_sale IN (0,1)),
                favorite_count       INTEGER NOT NULL DEFAULT 0  CHECK(favorite_count >= 0),
                created_by           INTEGER,
                created_at           TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at           TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
                FOREIGN KEY (created_by)  REFERENCES users(id)      ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS favorites (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'pending'
                                     CHECK(status IN ('pending','processing','completed','cancelled')),
                total_amount REAL    NOT NULL DEFAULT 0 CHECK(total_amount >= 0),
                notes        TEXT,
                admin_notes  TEXT,
                created_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                updated_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id           INTEGER NOT NULL,
                product_id         INTEGER NOT NULL,
                quantity           INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
                unit_price         REAL    NOT NULL CHECK(unit_price >= 0),
                gold_rate_at_order REAL,
                created_at         TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity   INTEGER NOT NULL DEFAULT 1 CHECK(quantity > 0),
                added_at   TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, product_id),
                FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS exchange_rates (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                usd_try          REAL    NOT NULL CHECK(usd_try > 0),
                eur_try          REAL    NOT NULL CHECK(eur_try > 0),
                gold_gram_try    REAL    NOT NULL CHECK(gold_gram_try > 0),
                gold_quarter_try REAL,
                gold_half_try    REAL,
                gold_full_try    REAL,
                source           TEXT    NOT NULL DEFAULT 'api' CHECK(source IN ('api','manual')),
                api_provider     TEXT,
                recorded_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                title          TEXT    NOT NULL,
                description    TEXT,
                discount_type  TEXT    NOT NULL CHECK(discount_type IN ('percentage','fixed','shipping')),
                discount_value REAL    NOT NULL DEFAULT 0 CHECK(discount_value >= 0),
                category       TEXT,
                start_date     TEXT    NOT NULL,
                end_date       TEXT    NOT NULL,
                badge          TEXT,
                image_path     TEXT,
                is_active      INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
                created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS activity_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                action      TEXT    NOT NULL,
                entity_type TEXT,
                entity_id   INTEGER,
                description TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category_id);
            CREATE INDEX IF NOT EXISTS idx_products_for_sale  ON products(is_for_sale);
            CREATE INDEX IF NOT EXISTS idx_favorites_user     ON favorites(user_id);
            CREATE INDEX IF NOT EXISTS idx_favorites_product  ON favorites(product_id);
            CREATE INDEX IF NOT EXISTS idx_orders_user        ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_order_items_order  ON order_items(order_id);
            CREATE INDEX IF NOT EXISTS idx_rates_recorded     ON exchange_rates(recorded_at);
            CREATE INDEX IF NOT EXISTS idx_cart_user          ON cart_items(user_id);
            CREATE INDEX IF NOT EXISTS idx_logs_user          ON activity_logs(user_id);
            CREATE INDEX IF NOT EXISTS idx_campaigns_active   ON campaigns(is_active);
            CREATE INDEX IF NOT EXISTS idx_campaigns_end_date ON campaigns(end_date);
        """)
        self._conn.commit()

    def _seed_defaults(self) -> None:
        """Varsayılan kategorileri ekler (ilk çalıştırmada)."""
        existing = self._conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if existing > 0:
            return

        default_categories = [
            ("Bilezik",      "bangle",   1),
            ("Yüzük",        "ring",     2),
            ("Kolye",        "necklace", 3),
            ("Küpe",         "earring",  4),
            ("Zincir",       "chain",    5),
            ("Set",          "set",      6),
            ("Çeyrek Altın", "coin",     7),
            ("Yarım Altın",  "coin",     8),
            ("Tam Altın",    "coin",     9),
            ("Gram Altın",   "coin",    10),
        ]
        self._conn.executemany(
            "INSERT OR IGNORE INTO categories (name, icon_name, display_order) VALUES (?, ?, ?)",
            default_categories,
        )
        self._conn.commit()
        logger.info("Varsayılan kategoriler eklendi.")
