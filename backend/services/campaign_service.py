"""
CampaignService — kampanya iş mantığı.
Otomatik pasifleştirme + aktif kampanyaları getirme.
"""

import logging
from typing import Optional

from backend.models.campaign import Campaign
from backend.repositories.campaign_repository import CampaignRepository

logger = logging.getLogger(__name__)


class CampaignService:

    def __init__(self, repo: CampaignRepository):
        self._repo = repo

    # ── Aktif kampanyalar ─────────────────────────────────────

    def get_active_campaigns(self) -> list[Campaign]:
        """Süresi dolanları pasife çekip aktif olanları döner."""
        removed = self._repo.deactivate_expired()
        if removed:
            logger.info("%d süresi dolan kampanya pasife çekildi.", removed)
        return self._repo.get_active()

    def get_all(self) -> list[Campaign]:
        return self._repo.get_all()

    def get_by_id(self, cid: int) -> Optional[Campaign]:
        return self._repo.get_by_id(cid)

    # ── Yönetim ───────────────────────────────────────────────

    def create(self, c: Campaign) -> Optional[Campaign]:
        return self._repo.create(c)

    def set_active(self, cid: int, active: bool) -> bool:
        return self._repo.set_active(cid, active)

    def delete(self, cid: int) -> bool:
        return self._repo.delete(cid)
