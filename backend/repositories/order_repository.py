import sqlite3
import logging
from typing import Optional

from backend.models.order import Order, OrderItem

logger = logging.getLogger(__name__)


# Tek noktadan SELECT sütun listesi — index'e bağımlı _to_model'i bozmadan
# yeni alanları sona ekliyoruz.
_ORDER_COLS = (
    "o.id, o.user_id, o.status, o.total_amount, o.notes, o.admin_notes, "
    "o.created_at, o.updated_at, "
    "o.shipping_amount, o.payment_method, o.order_number"
)


class OrderRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Create ────────────────────────────────────────────────

    def create(self, order: Order) -> Optional[Order]:
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO orders
                    (user_id, status, total_amount, shipping_amount,
                     payment_method, order_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order.user_id, order.status, order.total_amount,
                 order.shipping_amount or 0.0,
                 order.payment_method, order.order_number, order.notes),
            )
            order_id = cursor.lastrowid

            for item in order.items:
                self._conn.execute(
                    """
                    INSERT INTO order_items
                        (order_id, product_id, quantity, unit_price, gold_rate_at_order)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (order_id, item.product_id, item.quantity,
                     item.unit_price, item.gold_rate_at_order),
                )

            self._conn.commit()
            return self.get_by_id(order_id)
        except sqlite3.Error as e:
            logger.error("Sipariş oluşturma hatası: %s", e)
            return None

    def order_number_exists(self, order_number: str) -> bool:
        return self._conn.execute(
            "SELECT 1 FROM orders WHERE order_number = ?", (order_number,)
        ).fetchone() is not None

    # ── Read ──────────────────────────────────────────────────

    def get_by_id(self, order_id: int) -> Optional[Order]:
        row = self._conn.execute(
            f"""
            SELECT {_ORDER_COLS},
                   (u.first_name || ' ' || u.last_name) as user_full_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()
        if not row:
            return None
        order = self._to_model(row, has_user_name=True)
        order.items = self._get_items(order_id)
        return order

    def get_by_user(self, user_id: int) -> list[Order]:
        rows = self._conn.execute(
            f"SELECT {_ORDER_COLS} FROM orders o "
            "WHERE o.user_id = ? ORDER BY o.created_at DESC",
            (user_id,),
        ).fetchall()
        orders = [self._to_model(r, has_user_name=False) for r in rows]
        for o in orders:
            o.items = self._get_items(o.id)
        return orders

    def get_all(self) -> list[Order]:
        rows = self._conn.execute(
            f"""
            SELECT {_ORDER_COLS},
                   (u.first_name || ' ' || u.last_name) as user_full_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            """
        ).fetchall()
        return [self._to_model(r, has_user_name=True) for r in rows]

    def get_by_status(self, status: str) -> list[Order]:
        rows = self._conn.execute(
            f"""
            SELECT {_ORDER_COLS},
                   (u.first_name || ' ' || u.last_name) as user_full_name
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.id
            WHERE o.status = ?
            ORDER BY o.created_at DESC
            """,
            (status,),
        ).fetchall()
        return [self._to_model(r, has_user_name=True) for r in rows]

    def count_by_status(self, status: str) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status = ?", (status,)
        ).fetchone()[0]

    # ── Update ────────────────────────────────────────────────

    def update_status(self, order_id: int, status: str, admin_notes: Optional[str] = None) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE orders
                SET status = ?, admin_notes = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (status, admin_notes, order_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Sipariş durum güncelleme hatası: %s", e)
            return False

    # ── Private ───────────────────────────────────────────────

    def _get_items(self, order_id: int) -> list[OrderItem]:
        rows = self._conn.execute(
            """
            SELECT oi.*, p.name as product_name
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        ).fetchall()
        return [self._item_to_model(r) for r in rows]

    @staticmethod
    def _to_model(row, has_user_name: bool) -> Order:
        # Sütun sırası _ORDER_COLS ile birebir aynı.
        return Order(
            id=row[0], user_id=row[1], status=row[2],
            total_amount=row[3], notes=row[4], admin_notes=row[5],
            created_at=row[6], updated_at=row[7],
            shipping_amount=row[8] or 0.0,
            payment_method=row[9],
            order_number=row[10],
            user_full_name=row[11] if has_user_name and len(row) > 11 else None,
        )

    @staticmethod
    def _item_to_model(row) -> OrderItem:
        return OrderItem(
            id=row[0], order_id=row[1], product_id=row[2],
            quantity=row[3], unit_price=row[4],
            gold_rate_at_order=row[5], created_at=row[6],
            product_name=row[7] if len(row) > 7 else None,
        )
