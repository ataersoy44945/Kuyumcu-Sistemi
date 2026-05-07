import sqlite3
import logging
from typing import Optional

from backend.models.category import Category

logger = logging.getLogger(__name__)


class CategoryRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def create(self, category: Category) -> Optional[Category]:
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO categories (name, description, icon_name, display_order, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (category.name, category.description, category.icon_name,
                 category.display_order, int(category.is_active)),
            )
            self._conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError:
            logger.warning("Kategori zaten mevcut: %s", category.name)
            return None
        except sqlite3.Error as e:
            logger.error("Kategori oluşturma hatası: %s", e)
            return None

    def get_by_id(self, category_id: int) -> Optional[Category]:
        row = self._conn.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return self._to_model(row) if row else None

    def get_all(self) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories ORDER BY display_order, name"
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def get_active(self) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY display_order, name"
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def update(self, category: Category) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE categories
                SET name = ?, description = ?, icon_name = ?,
                    display_order = ?, is_active = ?
                WHERE id = ?
                """,
                (category.name, category.description, category.icon_name,
                 category.display_order, int(category.is_active), category.id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Kategori güncelleme hatası: %s", e)
            return False

    def delete(self, category_id: int) -> bool:
        try:
            self._conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self._conn.commit()
            return True
        except sqlite3.IntegrityError:
            logger.warning("Kategoriye bağlı ürünler var, silinemedi: id=%d", category_id)
            return False
        except sqlite3.Error as e:
            logger.error("Kategori silme hatası: %s", e)
            return False

    @staticmethod
    def _to_model(row) -> Category:
        return Category(
            id=row[0], name=row[1], description=row[2],
            icon_name=row[3], display_order=row[4],
            is_active=bool(row[5]), created_at=row[6],
        )
