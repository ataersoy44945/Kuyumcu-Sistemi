"""
CampaignRepository — campaigns tablosu için CRUD işlemleri.
"""

import logging
import sqlite3
from typing import Optional

from backend.models.campaign import Campaign

logger = logging.getLogger(__name__)


class CampaignRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Create ────────────────────────────────────────────────

    def create(self, c: Campaign) -> Optional[Campaign]:
        try:
            cur = self._conn.execute(
                """
                INSERT INTO campaigns
                    (title, description, discount_type, discount_value, category,
                     start_date, end_date, badge, image_path, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (c.title, c.description, c.discount_type, c.discount_value,
                 c.category, c.start_date, c.end_date, c.badge, c.image_path,
                 int(c.is_active)),
            )
            self._conn.commit()
            c.id = cur.lastrowid
            return c
        except sqlite3.Error as e:
            logger.error("Kampanya ekleme hatası: %s", e)
            return None

    # ── Read ──────────────────────────────────────────────────

    def get_all(self) -> list[Campaign]:
        rows = self._conn.execute(
            "SELECT * FROM campaigns ORDER BY is_active DESC, end_date ASC"
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def get_active(self) -> list[Campaign]:
        rows = self._conn.execute(
            """
            SELECT * FROM campaigns
            WHERE is_active = 1
              AND datetime(end_date) > datetime('now','localtime')
            ORDER BY end_date ASC
            """
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def get_by_id(self, campaign_id: int) -> Optional[Campaign]:
        row = self._conn.execute(
            "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
        ).fetchone()
        return self._to_model(row) if row else None

    # ── Update ────────────────────────────────────────────────

    def set_active(self, campaign_id: int, active: bool) -> bool:
        cur = self._conn.execute(
            "UPDATE campaigns SET is_active = ? WHERE id = ?",
            (int(active), campaign_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def deactivate_expired(self) -> int:
        """Süresi dolmuş aktif kampanyaları pasife çeker. Etkilenen satır sayısını döner."""
        cur = self._conn.execute(
            """
            UPDATE campaigns SET is_active = 0
            WHERE is_active = 1
              AND datetime(end_date) <= datetime('now','localtime')
            """
        )
        self._conn.commit()
        return cur.rowcount

    def delete(self, campaign_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
        self._conn.commit()
        return cur.rowcount > 0

    # ── Private ───────────────────────────────────────────────

    @staticmethod
    def _to_model(row) -> Campaign:
        return Campaign(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            discount_type=row["discount_type"],
            discount_value=row["discount_value"],
            category=row["category"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            badge=row["badge"],
            image_path=row["image_path"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )
