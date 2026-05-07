"""
SavedCardRepository — kullanıcıya ait kayıtlı kartlar için CRUD.
"""

import sqlite3
import logging
from typing import Optional

from backend.models.saved_card import SavedCard

logger = logging.getLogger(__name__)


class SavedCardRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Create ────────────────────────────────────────────────

    def create(self, card: SavedCard) -> Optional[SavedCard]:
        try:
            cur = self._conn.execute(
                """
                INSERT INTO saved_cards
                    (user_id, title, holder, bin, last4, brand,
                     expiry_mm, expiry_yy, is_default)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (card.user_id, card.title, card.holder,
                 card.bin, card.last4, card.brand,
                 card.expiry_mm, card.expiry_yy, int(card.is_default)),
            )
            self._conn.commit()
            return self.get_by_id(cur.lastrowid)
        except sqlite3.Error as e:
            logger.error("Kart kaydetme hatası: %s", e)
            return None

    # ── Read ──────────────────────────────────────────────────

    def get_by_id(self, card_id: int) -> Optional[SavedCard]:
        row = self._conn.execute(
            "SELECT * FROM saved_cards WHERE id = ?", (card_id,)
        ).fetchone()
        return self._to_model(row) if row else None

    def get_by_user(self, user_id: int) -> list[SavedCard]:
        rows = self._conn.execute(
            "SELECT * FROM saved_cards WHERE user_id = ? "
            "ORDER BY is_default DESC, created_at DESC",
            (user_id,),
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def find_existing(self, user_id: int, bin_: str, last4: str,
                      expiry_mm: int, expiry_yy: int) -> Optional[SavedCard]:
        """Aynı kart zaten kayıtlı mı? (BIN+last4+expiry yeterli)"""
        row = self._conn.execute(
            "SELECT * FROM saved_cards "
            "WHERE user_id=? AND bin=? AND last4=? AND expiry_mm=? AND expiry_yy=?",
            (user_id, bin_, last4, expiry_mm, expiry_yy),
        ).fetchone()
        return self._to_model(row) if row else None

    # ── Update ────────────────────────────────────────────────

    def set_default(self, user_id: int, card_id: int) -> bool:
        try:
            self._conn.execute(
                "UPDATE saved_cards SET is_default = 0 WHERE user_id = ?", (user_id,)
            )
            self._conn.execute(
                "UPDATE saved_cards SET is_default = 1 WHERE id = ? AND user_id = ?",
                (card_id, user_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Varsayılan kart güncelleme hatası: %s", e)
            return False

    # ── Delete ────────────────────────────────────────────────

    def delete(self, card_id: int, user_id: int) -> bool:
        try:
            cur = self._conn.execute(
                "DELETE FROM saved_cards WHERE id = ? AND user_id = ?",
                (card_id, user_id),
            )
            self._conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Kart silme hatası: %s", e)
            return False

    # ── Private ───────────────────────────────────────────────

    @staticmethod
    def _to_model(row: sqlite3.Row) -> SavedCard:
        return SavedCard(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            holder=row["holder"],
            bin=row["bin"],
            last4=row["last4"],
            brand=row["brand"],
            expiry_mm=int(row["expiry_mm"]),
            expiry_yy=int(row["expiry_yy"]),
            is_default=bool(row["is_default"]),
            created_at=row["created_at"],
        )
