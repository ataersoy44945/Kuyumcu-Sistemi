"""
SavedCardService — kart kaydetme iş mantığı.

PCI-DSS hatırlatması: Üretimde gerçek PAN ve CVV asla saklanmamalıdır.
Bu servis sadece BIN + son 4 hane + son kullanma + sahip bilgisini kaydeder.
Tam kart numarası SADECE kaydetme anında parçalama için alınır, hiçbir
yere yazılmaz.
"""

import logging
import re
from typing import Optional

from backend.models.saved_card import SavedCard, detect_brand
from backend.repositories.saved_card_repository import SavedCardRepository

logger = logging.getLogger(__name__)


class SavedCardService:

    def __init__(self, repo: SavedCardRepository):
        self._repo = repo

    # ── Read ─────────────────────────────────────────────────

    def list_for_user(self, user_id: int) -> list[SavedCard]:
        return self._repo.get_by_user(user_id)

    # ── Write ────────────────────────────────────────────────

    def save_card(
        self,
        user_id:     int,
        holder:      str,
        card_number: str,
        expiry_mm:   int,
        expiry_yy:   int,
        title:       Optional[str] = None,
        make_default: bool = False,
    ) -> SavedCard:
        """
        Yeni bir kart kaydeder. card_number sadece BIN+last4 çıkarmak için
        kullanılır, saklanmaz.
        Aynı kart (BIN+last4+expiry) zaten varsa mevcut kayıt döner.
        """
        digits = re.sub(r"\D", "", card_number or "")
        if len(digits) < 13 or len(digits) > 19:
            raise ValueError("Geçersiz kart numarası uzunluğu.")
        if not (1 <= int(expiry_mm) <= 12):
            raise ValueError("Geçersiz son kullanma ayı.")
        if not (0 <= int(expiry_yy) <= 99):
            raise ValueError("Geçersiz son kullanma yılı.")
        if not holder or not holder.strip():
            raise ValueError("Kart sahibi boş olamaz.")

        bin_  = digits[:6]
        last4 = digits[-4:]
        brand = detect_brand(digits)
        title = (title or "").strip() or None
        holder = holder.strip().upper()

        # Aynı kart zaten kayıtlıysa onu döner — kullanıcıyı şaşırtma
        existing = self._repo.find_existing(user_id, bin_, last4,
                                              int(expiry_mm), int(expiry_yy))
        if existing:
            logger.info("Kart zaten kayıtlı (id=%d) — yeniden eklenmedi.", existing.id)
            if make_default and not existing.is_default:
                self._repo.set_default(user_id, existing.id)
            return existing

        # İlk kayıt otomatik varsayılan olur
        is_default = make_default or not self._repo.get_by_user(user_id)

        card = SavedCard(
            user_id=user_id, holder=holder,
            bin=bin_, last4=last4, brand=brand,
            expiry_mm=int(expiry_mm), expiry_yy=int(expiry_yy),
            title=title, is_default=is_default,
        )
        created = self._repo.create(card)
        if created is None:
            raise RuntimeError("Kart kaydedilemedi.")

        # Varsayılan yapıldıysa diğerlerini sıfırla
        if is_default:
            self._repo.set_default(user_id, created.id)
            created.is_default = True

        logger.info("Kart kaydedildi: user=%d brand=%s last4=%s",
                    user_id, brand, last4)
        return created

    def set_default(self, user_id: int, card_id: int) -> bool:
        return self._repo.set_default(user_id, card_id)

    def delete(self, user_id: int, card_id: int) -> bool:
        return self._repo.delete(card_id, user_id)
