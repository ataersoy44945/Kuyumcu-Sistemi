"""
FavoriteService — Favori ekleme/çıkarma iş mantığı.
Favori sayacı senkronizasyonunu da yönetir.
"""

import logging

from backend.models.product import Product
from backend.repositories.favorite_repository import FavoriteRepository
from backend.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class FavoriteService:

    def __init__(self, favorite_repo: FavoriteRepository, product_repo: ProductRepository):
        self._favorites = favorite_repo
        self._products  = product_repo

    def toggle(self, user_id: int, product_id: int) -> bool:
        """
        Favoriye ekler ya da çıkarır.

        Returns:
            True  → ürün favorilere eklendi
            False → ürün favorilerden çıkarıldı
        """
        if self._favorites.is_favorite(user_id, product_id):
            self._favorites.remove(user_id, product_id)
            self._products.update_favorite_count(product_id, delta=-1)
            logger.debug("Favoriden çıkarıldı: user=%d product=%d", user_id, product_id)
            return False
        else:
            self._favorites.add(user_id, product_id)
            self._products.update_favorite_count(product_id, delta=+1)
            logger.debug("Favoriye eklendi: user=%d product=%d", user_id, product_id)
            return True

    def get_user_favorites(self, user_id: int) -> list[Product]:
        return self._favorites.get_products_by_user(user_id)

    def is_favorite(self, user_id: int, product_id: int) -> bool:
        return self._favorites.is_favorite(user_id, product_id)
