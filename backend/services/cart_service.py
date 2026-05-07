"""
CartService — sepet iş mantığı.

Merkezi sepet API'si:
  - add_to_cart(user_id, product_id)  → aynı ürün tekrar eklenirse adet artar
  - remove_from_cart(user_id, product_id)
  - update_quantity(user_id, product_id, quantity)
  - get_cart_items(user_id)           → ürün bilgisiyle birlikte satırlar
  - cart_count(user_id)               → toplam adet (rozet için)
  - clear_cart(user_id)
"""

import logging
import sqlite3

from backend.models.product import Product

logger = logging.getLogger(__name__)


class CartService:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Yazma işlemleri ──────────────────────────────────────

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> int:
        """Sepete ekler; mevcut kayıt varsa adedi artırır. Yeni adet döner."""
        if quantity <= 0:
            return 0

        row = self._conn.execute(
            "SELECT quantity FROM cart_items WHERE user_id=? AND product_id=?",
            (user_id, product_id),
        ).fetchone()

        if row:
            new_qty = int(row["quantity"]) + quantity
            self._conn.execute(
                "UPDATE cart_items SET quantity=? WHERE user_id=? AND product_id=?",
                (new_qty, user_id, product_id),
            )
        else:
            new_qty = quantity
            self._conn.execute(
                """INSERT INTO cart_items (user_id, product_id, quantity)
                   VALUES (?, ?, ?)""",
                (user_id, product_id, quantity),
            )
        self._conn.commit()
        logger.info("Sepete eklendi: user=%d product=%d qty=%d", user_id, product_id, new_qty)
        return new_qty

    def remove_from_cart(self, user_id: int, product_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM cart_items WHERE user_id=? AND product_id=?",
            (user_id, product_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def update_quantity(self, user_id: int, product_id: int, quantity: int) -> bool:
        if quantity <= 0:
            return self.remove_from_cart(user_id, product_id)
        cur = self._conn.execute(
            "UPDATE cart_items SET quantity=? WHERE user_id=? AND product_id=?",
            (quantity, user_id, product_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def clear_cart(self, user_id: int) -> int:
        cur = self._conn.execute(
            "DELETE FROM cart_items WHERE user_id=?", (user_id,)
        )
        self._conn.commit()
        return cur.rowcount

    # ── Okuma işlemleri ──────────────────────────────────────

    def get_cart_items(self, user_id: int) -> list[dict]:
        """
        Sepetteki tüm ürünleri ürün detaylarıyla birlikte döner.
        Her item: {product: Product, quantity: int}
        """
        rows = self._conn.execute(
            """
            SELECT ci.quantity,
                   p.id, p.name, p.category_id, p.description,
                   p.weight_grams, p.karat, p.karat_coefficient,
                   p.labor_cost, p.profit_margin, p.base_price,
                   p.use_calculated_price, p.stock_quantity,
                   p.image_path, p.is_for_sale,
                   c.name AS category_name
            FROM cart_items ci
            JOIN products   p ON ci.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE ci.user_id = ?
            ORDER BY ci.added_at DESC
            """,
            (user_id,),
        ).fetchall()

        items = []
        for r in rows:
            p = Product(
                id=r["id"], name=r["name"], category_id=r["category_id"],
                description=r["description"],
                weight_grams=r["weight_grams"], karat=r["karat"],
                karat_coefficient=r["karat_coefficient"],
                labor_cost=r["labor_cost"], profit_margin=r["profit_margin"],
                base_price=r["base_price"],
                use_calculated_price=bool(r["use_calculated_price"]),
                stock_quantity=r["stock_quantity"],
                image_path=r["image_path"],
                is_for_sale=bool(r["is_for_sale"]),
                category_name=r["category_name"],
            )
            items.append({"product": p, "quantity": int(r["quantity"])})
        return items

    def cart_count(self, user_id: int) -> int:
        """Sepetteki toplam ürün adedi (rozet için)."""
        row = self._conn.execute(
            "SELECT COALESCE(SUM(quantity),0) AS c FROM cart_items WHERE user_id=?",
            (user_id,),
        ).fetchone()
        return int(row["c"])
