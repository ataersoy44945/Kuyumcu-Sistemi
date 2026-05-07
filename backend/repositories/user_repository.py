"""
UserRepository — users tablosuna tek yetkili erişim noktası.
"""

import sqlite3
import logging
from typing import Optional

from backend.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    # ── Create ────────────────────────────────────────────────

    def create(self, user: User, password_hash: str) -> Optional[User]:
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO users
                    (username, email, password_hash, role, first_name, last_name, phone, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user.username, user.email, password_hash, user.role,
                 user.first_name, user.last_name, user.phone, int(user.is_active)),
            )
            self._conn.commit()
            return self.get_by_id(cursor.lastrowid)
        except sqlite3.IntegrityError as e:
            logger.warning("Kullanıcı oluşturulamadı (benzersizlik ihlali): %s", e)
            return None
        except sqlite3.Error as e:
            logger.error("Kullanıcı oluşturma hatası: %s", e)
            return None

    # ── Read ──────────────────────────────────────────────────

    def get_by_id(self, user_id: int) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return self._to_model(row) if row else None

    def get_by_username(self, username: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return self._to_model(row) if row else None

    def get_by_email(self, email: str) -> Optional[User]:
        row = self._conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return self._to_model(row) if row else None

    def get_password_hash(self, user_id: int) -> Optional[str]:
        row = self._conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return row[0] if row else None

    def get_all(self) -> list[User]:
        rows = self._conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
        return [self._to_model(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'customer'"
        ).fetchone()[0]

    # ── Update ────────────────────────────────────────────────

    def update(self, user: User) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE users
                SET first_name = ?, last_name = ?, phone = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (user.first_name, user.last_name, user.phone, user.id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Kullanıcı güncelleme hatası: %s", e)
            return False

    def update_password(self, user_id: int, new_hash: str) -> bool:
        try:
            self._conn.execute(
                """
                UPDATE users
                SET password_hash = ?, updated_at = datetime('now', 'localtime')
                WHERE id = ?
                """,
                (new_hash, user_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Şifre güncelleme hatası: %s", e)
            return False

    def set_active(self, user_id: int, is_active: bool) -> bool:
        try:
            self._conn.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (int(is_active), user_id),
            )
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Kullanıcı aktiflik güncelleme hatası: %s", e)
            return False

    def update_last_login(self, user_id: int) -> None:
        try:
            self._conn.execute(
                "UPDATE users SET last_login_at = datetime('now', 'localtime') WHERE id = ?",
                (user_id,),
            )
            self._conn.commit()
        except sqlite3.Error as e:
            logger.error("Son giriş güncelleme hatası: %s", e)

    # ── Delete ────────────────────────────────────────────────

    def delete(self, user_id: int) -> bool:
        try:
            self._conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error("Kullanıcı silme hatası: %s", e)
            return False

    # ── Private ───────────────────────────────────────────────

    @staticmethod
    def _to_model(row: sqlite3.Row) -> User:
        return User(
            id=row[0], username=row[1], email=row[2],
            password_hash=row[3], role=row[4],
            first_name=row[5], last_name=row[6],
            phone=row[7], is_active=bool(row[8]),
            created_at=row[9], updated_at=row[10], last_login_at=row[11],
        )
