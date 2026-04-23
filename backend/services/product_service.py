"""
ProductService — Ürün ve kategori iş mantığı.
"""

import logging
from typing import Optional

from config import KARAT_COEFFICIENTS, DEFAULT_PROFIT_MARGIN, LOW_STOCK_THRESHOLD
from backend.models.product import Product
from backend.models.category import Category
from backend.repositories.product_repository import ProductRepository
from backend.repositories.category_repository import CategoryRepository
from backend.utils.validators import (
    validate_positive_float, validate_non_negative_float,
    validate_non_negative_int, validate_karat, validate_profit_margin,
)

logger = logging.getLogger(__name__)


class ProductService:

    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self._products    = product_repo
        self._categories  = category_repo

    # ── Ürün Sorgulama (kullanıcı + admin) ────────────────────

    def get_all(self, for_sale_only: bool = True) -> list[Product]:
        return self._products.get_all(for_sale_only=for_sale_only)

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self._products.get_by_id(product_id)

    def search(
        self,
        query: str = "",
        karat: Optional[str] = None,
        category_id: Optional[int] = None,
        for_sale_only: bool = True,
    ) -> list[Product]:
        return self._products.search(query, karat, category_id, for_sale_only)

    def get_most_favorited(self, limit: int = 5) -> list[Product]:
        return self._products.get_most_favorited(limit)

    def get_low_stock(self) -> list[Product]:
        return self._products.get_low_stock(LOW_STOCK_THRESHOLD)

    # ── Admin: Ürün Yönetimi ──────────────────────────────────

    def add_product(self, data: dict, admin_id: int) -> Product:
        """
        Yeni ürün ekler. data dict'i formdan gelen ham değerleri içerir.
        Hatalı girişlerde ValidationError fırlatır.
        """
        karat = validate_karat(str(data.get("karat", "")))

        product = Product(
            name=str(data["name"]).strip(),
            category_id=int(data["category_id"]),
            weight_grams=validate_positive_float(float(data["weight_grams"]), "Gram"),
            karat=karat,
            karat_coefficient=KARAT_COEFFICIENTS[karat],
            description=data.get("description", ""),
            labor_cost=validate_non_negative_float(float(data.get("labor_cost", 0)), "İşçilik"),
            profit_margin=validate_profit_margin(float(data.get("profit_margin", DEFAULT_PROFIT_MARGIN))),
            base_price=float(data["base_price"]) if data.get("base_price") else None,
            use_calculated_price=bool(data.get("use_calculated_price", True)),
            stock_quantity=validate_non_negative_int(int(data.get("stock_quantity", 0)), "Stok"),
            image_path=data.get("image_path"),
            is_for_sale=bool(data.get("is_for_sale", True)),
            created_by=admin_id,
        )

        created = self._products.create(product)
        if created is None:
            raise RuntimeError("Ürün kaydedilemedi.")
        logger.info("Ürün eklendi: %s (id=%d)", created.name, created.id)
        return created

    def update_product(self, product_id: int, data: dict) -> bool:
        product = self._products.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Ürün bulunamadı: id={product_id}")

        karat = validate_karat(str(data.get("karat", product.karat)))

        product.name               = str(data.get("name", product.name)).strip()
        product.category_id        = int(data.get("category_id", product.category_id))
        product.weight_grams       = validate_positive_float(float(data.get("weight_grams", product.weight_grams)), "Gram")
        product.karat              = karat
        product.karat_coefficient  = KARAT_COEFFICIENTS[karat]
        product.description        = data.get("description", product.description)
        product.labor_cost         = validate_non_negative_float(float(data.get("labor_cost", product.labor_cost)), "İşçilik")
        product.profit_margin      = validate_profit_margin(float(data.get("profit_margin", product.profit_margin)))
        product.base_price         = float(data["base_price"]) if data.get("base_price") else None
        product.use_calculated_price = bool(data.get("use_calculated_price", product.use_calculated_price))
        product.stock_quantity     = validate_non_negative_int(int(data.get("stock_quantity", product.stock_quantity)), "Stok")
        product.image_path         = data.get("image_path", product.image_path)
        product.is_for_sale        = bool(data.get("is_for_sale", product.is_for_sale))

        return self._products.update(product)

    def delete_product(self, product_id: int) -> bool:
        return self._products.delete(product_id)

    def update_stock(self, product_id: int, quantity: int) -> bool:
        validate_non_negative_int(quantity, "Stok")
        return self._products.update_stock(product_id, quantity)

    # ── Kategori Yönetimi ─────────────────────────────────────

    def get_categories(self, active_only: bool = True) -> list[Category]:
        return self._categories.get_active() if active_only else self._categories.get_all()

    def get_categories_with_counts(self, active_only: bool = True) -> list[dict]:
        """
        Her kategori için ürün sayısıyla birlikte döner.
        [{"category": Category, "product_count": int}, ...]
        """
        cats = self.get_categories(active_only=active_only)
        result = []
        for c in cats:
            count = len([p for p in self._products.get_all(for_sale_only=False)
                         if p.category_id == c.id])
            result.append({"category": c, "product_count": count})
        return result

    def add_category(self, name: str, description: str = "", icon_name: str = "") -> Category:
        cat = Category(name=name.strip(), description=description, icon_name=icon_name or None)
        created = self._categories.create(cat)
        if created is None:
            raise ValueError(f"'{name}' kategorisi zaten mevcut.")
        return created

    def update_category(self, category_id: int, name: str, description: str = "") -> bool:
        cat = self._categories.get_by_id(category_id)
        if cat is None:
            raise ValueError("Kategori bulunamadı.")
        cat.name = name.strip()
        cat.description = description
        return self._categories.update(cat)

    def delete_category(self, category_id: int) -> bool:
        return self._categories.delete(category_id)

    # ── İstatistikler (admin dashboard) ───────────────────────

    def get_statistics(self) -> dict:
        return {
            "total":        self._products.count(),
            "in_stock":     self._products.count_in_stock(),
            "out_of_stock": self._products.count_out_of_stock(),
            "low_stock":    len(self.get_low_stock()),
        }
