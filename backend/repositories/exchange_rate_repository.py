import sqlite3
import logging
from typing import Optional

from backend.models.exchange_rate import ExchangeRateData

logger = logging.getLogger(__name__)


class ExchangeRateRepository:

    def __init__(self, connection: sqlite3.Connection):
        self._conn = connection

    def save(self, data: ExchangeRateData) -> int:
        try:
            cursor = self._conn.execute(
                """
                INSERT INTO exchange_rates
                    (usd_try, eur_try, gold_gram_try, gold_quarter_try,
                     gold_half_try, gold_full_try, source, api_provider, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.usd_try, data.eur_try, data.gold_gram_try,
                    data.gold_quarter_try, data.gold_half_try, data.gold_full_try,
                    data.source, data.api_provider, data.recorded_at,
                ),
            )
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("Kur kaydedilemedi: %s", e)
            return -1

    def get_latest(self) -> Optional[ExchangeRateData]:
        row = self._conn.execute(
            """
            SELECT usd_try, eur_try, gold_gram_try, gold_quarter_try,
                   gold_half_try, gold_full_try, source, api_provider, recorded_at
            FROM exchange_rates ORDER BY id DESC LIMIT 1
            """
        ).fetchone()
        return self._to_model(row) if row else None

    def get_history(self, limit: int = 50) -> list[ExchangeRateData]:
        rows = self._conn.execute(
            """
            SELECT usd_try, eur_try, gold_gram_try, gold_quarter_try,
                   gold_half_try, gold_full_try, source, api_provider, recorded_at
            FROM exchange_rates ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_model(r) for r in rows]

    @staticmethod
    def _to_model(row) -> ExchangeRateData:
        return ExchangeRateData(
            usd_try=row[0], eur_try=row[1], gold_gram_try=row[2],
            gold_quarter_try=row[3], gold_half_try=row[4], gold_full_try=row[5],
            source=row[6], api_provider=row[7] or "", recorded_at=row[8],
        )
