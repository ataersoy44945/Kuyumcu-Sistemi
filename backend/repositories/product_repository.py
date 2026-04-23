"""
ProductRepository — products tablosuna tek yetkili erişim noktası.
"""

import sqlite3
import logging
from typing import Optional

from backend.models.product import Product

logger = logging.getLogger(__name__)


class ProductRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Create ────────────────────────────────────────────────

    def create(self, product: Product) -> Optional[Product]:
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO products
                    (category_id, name, description, weight_grams, karat, karat_coefficient,
                     labor_cost, profit_margin, base_price, use_calculated_price,
                     stock_quantity, image_path, is_for_sale, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product.category_id, product.name, product.description,
                    product.weight_grams, product.karat, product.karat_coefficient,
                    product.labor_cost, product.profit_margin, product.base_price,
                    int(product.use_calculated_price), product.stock_quantity,
                    product.image_path, int(product.is_for_sale), product.created_by,
                ),
            )
            self._conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.Error as e:
            logger.error("Ürün oluşturma hatası: %s", e)
            return None

    # ── Read ──────────────────────────────────────────────────

    def get_by_id(self, product_id: int) -> Optional[Product]:
        row = self._conn.execute(
            """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()
        return self._to_model(row) if row else None

    def get_all(self, for_sale_only: bool = False) -> list[Product]:
        query = """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
        """
        if for_sale_only:
            query += " WHERE p.is_for_sale = 1"
        query += " ORDER BY p.created_at DESC"
        rows = self._conn.execute(query).fetchall()
        return [self._to_model(r) for r in rows]

    def get_by_category(self, category_id: int, for_sale_only: bool = True) -> list[Product]:
        where = "WHERE p.category_id = ?"
        params: list = [category_id]
        if for_sale_only:
            where += " AND p.is_for_sale = 1"
        rows = self._conn.execute(
            f"""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where}
            ORDER BY p.name
            """,
            params,
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def search(
        self,
        query: str = "",
        karat: Optional[str] = None,
        category_id: Optional[int] = None,
        for_sale_only: bool = True,
    ) -> list[Product]:
        conditions = []
        params: list = []

        if for_sale_only:
            conditions.append("p.is_for_sale = 1")

        if query:
            conditions.append("(p.name LIKE ? OR p.description LIKE ?)")
            params += [f"%{query}%", f"%{query}%"]

        if karat:
            conditions.append("p.karat = ?")
            params.append(karat)

        if category_id is not None:
            conditions.append("p.category_id = ?")
            params.append(category_id)

        where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = self._conn.execute(
            f"""
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {where_clause}
            ORDER BY p.name
            """,
            params,
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def get_most_favorited(self, limit: int = 5) -> list[Product]:
        rows = self._conn.execute(
            """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_for_sale = 1
            ORDER BY p.favorite_count DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def get_low_stock(self, threshold: int = 3) -> list[Product]:
        rows = self._conn.execute(
            """
            SELECT p.*, c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock_quantity > 0 AND p.stock_quantity <= ?
            ORDER BY p.stock_quantity ASC
            """,
            (threshold,),
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    def count_in_stock(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock_quantity > 0"
        ).fetchone()[0]

    def count_out_of_stock(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock_quantity = 0"
        ).fetchone()[0]

    # ── Update ────────────────────────────────────────────────

    def update(self, product: Product) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE products SET
                    category_id = ?, name = ?, description = ?,
                    weight_grams = ?, karat = ?, karat_coefficient = ?,
                    labor_cost = ?, profit_margin = ?, base_price = ?,
                    use_calculated_price = ?, stock_quantity = ?,
                    image_path = ?, is_for_sale = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (
                    product.category_id, product.name, product.description,
                    product.weight_grams, product.karat, product.karat_coefficient,
                    product.labor_cost, product.profit_margin, product.base_price,
                    int(product.use_calculated_price), product.stock_quantity,
                    product.image_path, int(product.is_for_sale), product.id,
                ),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Ürün güncelleme hatası: %s", e)
            return False

    def update_stock(self, product_id: int, quantity: int) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE products SET stock_quantity = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (quantity, product_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Stok güncelleme hatası: %s", e)
            return False

    def update_favorite_count(self, product_id: int, delta: int) -> None:
        """Favori sayacını delta kadar artırır/azaltır (delta = +1 ya da -1)."""
        try:
            self._conn.execute(
                """
                UPDATE products
                SET favorite_count = MAX(0, favorite_count + ?)
                WHERE id = ?
                """,
                (delta, product_id),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error("Favori sayısı güncelleme hatası: %s", e)

    # ── Delete ────────────────────────────────────────────────

    def delete(self, product_id: int) -> bool:
        try:
            self._conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Ürün silme hatası: %s", e)
            return False

    # ── Private ───────────────────────────────────────────────

    @staticmethod
    def _to_model(row) -> Product:
        return Product(
            id=row[0], category_id=row[1], name=row[2], description=row[3],
            weight_grams=row[4], karat=row[5], karat_coefficient=row[6],
            labor_cost=row[7], profit_margin=row[8], base_price=row[9],
            use_calculated_price=bool(row[10]), stock_quantity=row[11],
            image_path=row[12], is_for_sale=bool(row[13]),
            favorite_count=row[14], created_by=row[15],
            created_at=row[16], updated_at=row[17],
            category_name=row[18] if len(row) > 18 else None,
        )
