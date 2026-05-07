"""
ExchangeRateAPI — Sadece HTTP istekleri.
İş mantığı, önbellek veya DB bu dosyada yoktur.
Service katmanı bu client'ı kullanır.
"""

import logging
from typing import Any, Optional, cast

import requests
from requests.exceptions import (
    ConnectionError as ReqConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)

from config import EXCHANGE_RATE_TIMEOUT_SEC

logger = logging.getLogger(__name__)

# Birincil: Türkiye'ye özel, altın dahil tüm kurlar
_PRIMARY_URL:  str = "https://finans.truncgil.com/today.json"
# Yedek: Genel döviz, altın verisi yok
_FALLBACK_URL: str = "https://api.exchangerate-api.com/v4/latest/USD"
# BTC anlık fiyat (Binance public endpoint)
_BTC_URL:      str = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"


class ExchangeRateAPI:
    """
    Ham kur verisini API'den çeken HTTP client.
    Dönen dict'ler service katmanında parse edilir.
    """

    def fetch_primary(self) -> Optional[dict[str, Any]]:
        """finans.truncgil.com'dan ham JSON döner. Hata varsa None."""
        return self._get(_PRIMARY_URL, "birincil")

    def fetch_fallback(self) -> Optional[dict[str, Any]]:
        """exchangerate-api.com'dan ham JSON döner. Hata varsa None."""
        return self._get(_FALLBACK_URL, "yedek")

    def fetch_btc(self) -> Optional[dict[str, Any]]:
        """Binance'ten BTC/USDT anlık fiyatı çeker. {"symbol": …, "price": "…"}"""
        return self._get(_BTC_URL, "btc")

    # ──────────────────────────────────────────────────────────
    # Private
    # ──────────────────────────────────────────────────────────

    def _get(self, url: str, label: str) -> Optional[dict[str, Any]]:
        try:
            response = requests.get(url, timeout=EXCHANGE_RATE_TIMEOUT_SEC)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return cast(dict[str, Any], data)
            logger.warning("%s API beklenmeyen JSON tipi: %s", label, type(data).__name__)
            return None
        except Timeout:
            logger.warning("%s API zaman aşımı: %s", label, url)
        except ReqConnectionError:
            logger.warning("%s API bağlantı hatası: %s", label, url)
        except HTTPError as e:
            logger.warning("%s API HTTP hatası: %s", label, e)
        except RequestException as e:
            logger.warning("%s API istek hatası: %s", label, e)
        except Exception as e:   # pragma: no cover
            logger.error("%s API beklenmedik hata: %s", label, e)
        return None
