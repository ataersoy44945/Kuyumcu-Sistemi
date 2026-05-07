"""
ExchangeRateService — Döviz ve altın kuru iş mantığı.
API client ile DB arasındaki köprü; önbellek, fallback ve manuel override burada.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from config import EXCHANGE_RATE_CACHE_MINUTES, GOLD_WEIGHTS
from backend.models.exchange_rate import ExchangeRateData
from backend.api.exchange_rate_api import ExchangeRateAPI
from backend.repositories.exchange_rate_repository import ExchangeRateRepository

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """
    Kur verisi için tek yetkili erişim noktası.

    Zincir:
      1. Bellek önbelleği (EXCHANGE_RATE_CACHE_MINUTES TTL)
      2. Birincil API   (finans.truncgil.com)
      3. Yedek API      (exchangerate-api.com)
      4. DB'deki son kayıt (offline fallback)
    """

    def __init__(self, api: ExchangeRateAPI, repository: ExchangeRateRepository):
        self._api   = api
        self._repo  = repository
        self._cache: Optional[ExchangeRateData] = None
        self._cache_time: Optional[datetime]    = None

    # ── Public ────────────────────────────────────────────────

    def get_rates(self) -> Optional[ExchangeRateData]:
        if self._is_cache_valid():
            return self._cache

        data = self._fetch_primary() or self._fetch_fallback()

        if data:
            self._set_cache(data)
            self._repo.save(data)
        else:
            data = self._repo.get_latest()
            if data:
                logger.warning("API erişilemez — DB'deki son kur kullanılıyor (%s).", data.recorded_at)

        return data

    def refresh(self) -> Optional[ExchangeRateData]:
        """Admin 'Yenile' butonundan çağrılır — önbelleği atlayarak zorla günceller."""
        self._clear_cache()
        return self.get_rates()

    def set_manual(self, usd_try: float, eur_try: float, gold_gram_try: float) -> ExchangeRateData:
        """Admin manuel kur girişi. Türev değerler otomatik hesaplanır."""
        data = ExchangeRateData(
            usd_try=usd_try,
            eur_try=eur_try,
            gold_gram_try=gold_gram_try,
            gold_quarter_try=round(gold_gram_try * GOLD_WEIGHTS["ceyrek_altin"], 2),
            gold_half_try=round(gold_gram_try * GOLD_WEIGHTS["yarim_altin"], 2),
            gold_full_try=round(gold_gram_try * GOLD_WEIGHTS["tam_altin"], 2),
            source="manual",
            api_provider="manuel giriş",
        )
        self._set_cache(data)
        self._repo.save(data)
        logger.info("Manuel kur girildi: USD=%.4f EUR=%.4f ALTIN=%.2f", usd_try, eur_try, gold_gram_try)
        return data

    def last_update_label(self) -> str:
        if self._cache:
            return f"Son güncelleme: {self._cache.display_update_time()}"
        return "Kur verisi mevcut değil"

    def get_history(self, limit: int = 50) -> list[ExchangeRateData]:
        return self._repo.get_history(limit)

    # ── Private — Cache ───────────────────────────────────────

    def _is_cache_valid(self) -> bool:
        if self._cache is None or self._cache_time is None:
            return False
        return datetime.now() - self._cache_time < timedelta(minutes=EXCHANGE_RATE_CACHE_MINUTES)

    def _set_cache(self, data: ExchangeRateData) -> None:
        self._cache = data
        self._cache_time = datetime.now()

    def _clear_cache(self) -> None:
        self._cache = None
        self._cache_time = None

    # ── Private — Fetch ───────────────────────────────────────

    def _fetch_primary(self) -> Optional[ExchangeRateData]:
        raw = self._api.fetch_primary()
        if raw is None:
            return None
        return self._parse_primary(raw)

    def _parse_primary(self, raw: dict) -> Optional[ExchangeRateData]:
        try:
            def tf(text: str) -> float:
                return float(str(text).replace(".", "").replace(",", "."))

            data = ExchangeRateData(
                usd_try=tf(raw["USD"]["Satış"]),
                eur_try=tf(raw["EUR"]["Satış"]),
                gold_gram_try=tf(raw["gram-altin"]["Satış"]),
                gold_quarter_try=tf(raw["ceyrek-altin"]["Satış"]),
                gold_half_try=tf(raw["yarim-altin"]["Satış"]),
                gold_full_try=tf(raw["tam-altin"]["Satış"]),
                source="api",
                api_provider="finans.truncgil.com",
            )
            logger.info("Kur birincil API'den alındı.")
            return data
        except (KeyError, ValueError, TypeError) as e:
            logger.error("Birincil API parse hatası: %s", e)
            return None

    def _fetch_fallback(self) -> Optional[ExchangeRateData]:
        raw = self._api.fetch_fallback()
        if raw is None:
            return None
        return self._parse_fallback(raw)

    def _parse_fallback(self, raw: dict) -> Optional[ExchangeRateData]:
        try:
            rates   = raw.get("rates", {})
            usd_try = float(rates["TRY"])
            eur_usd = float(rates["EUR"])
            eur_try = usd_try / eur_usd

            last      = self._repo.get_latest()
            gold_gram = last.gold_gram_try if last else 0.0

            data = ExchangeRateData(
                usd_try=round(usd_try, 4),
                eur_try=round(eur_try, 4),
                gold_gram_try=gold_gram,
                gold_quarter_try=round(gold_gram * GOLD_WEIGHTS["ceyrek_altin"], 2) if gold_gram else None,
                gold_half_try=round(gold_gram * GOLD_WEIGHTS["yarim_altin"], 2) if gold_gram else None,
                gold_full_try=round(gold_gram * GOLD_WEIGHTS["tam_altin"], 2) if gold_gram else None,
                source="api",
                api_provider="exchangerate-api.com (yedek)",
            )
            logger.info("Kur yedek API'den alındı (altın verisi DB'den tamamlandı).")
            return data
        except (KeyError, ValueError, ZeroDivisionError) as e:
            logger.error("Yedek API parse hatası: %s", e)
            return None
