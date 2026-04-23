from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExchangeRateData:
    """
    Döviz ve altın kuru verisi.
    API, DB veya manuel giriş fark etmeksizin aynı yapıyla taşınır.
    """

    usd_try:       float
    eur_try:       float
    gold_gram_try: float

    gold_quarter_try: Optional[float] = None
    gold_half_try:    Optional[float] = None
    gold_full_try:    Optional[float] = None

    source:       str = "api"     # "api" | "manual" | "db_fallback"
    api_provider: str = ""
    recorded_at:  str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def display_update_time(self) -> str:
        try:
            dt = datetime.strptime(self.recorded_at, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return self.recorded_at

    def is_complete(self) -> bool:
        """Kritik alanların tamamı dolu mu?"""
        return bool(self.usd_try and self.eur_try and self.gold_gram_try)
