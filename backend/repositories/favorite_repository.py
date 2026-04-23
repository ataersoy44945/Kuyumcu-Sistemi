import sqlite3
import logging

from backend.models.product import Product

logger = logging.getLogger(__name__)


class FavoriteRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def add(self, user_id: int, product_id: int) -> bool:
        """Favoriye ekler. Zaten varsa sessizce geçer."""
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO favorites (user_id, product_id) VALUES (?, ?)",
                (user_id, product_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Favori ekleme hatası: %s", e)
            return False

    def remove(self, user_id: int, product_id: int) -> bool:
        try:
            self._conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
                (user_id, product_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Favori kaldırma hatası: %s", e)
            return False

    def is_favorite(self, user_id: int, product_id: int) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        return row is not None

    def get_products_by_user(self, user_id: int) -> list[Product]:
        """Kullanıcının favori ürünlerini Product listesi olarak döner."""
        from backend.repositories.product_repository import ProductRepository
        rows = self._conn.execute(
            """
            SELECT p.*, c.name as category_name
            FROM favorites f
            JOIN products p ON f.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE f.user_id = ?
            ORDER BY f.created_at DESC
            """,
            (user_id,),
        ).fetchall()
        return [ProductRepository._to_model(r) for r in rows]

    def count_by_product(self, product_id: int) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM favorites WHERE product_id = ?", (product_id,)
        ).fetchone()[0]
