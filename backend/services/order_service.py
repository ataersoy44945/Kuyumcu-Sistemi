"""
OrderService — Sipariş oluşturma ve yönetim iş mantığı.
"""

import logging
import random
from datetime import datetime
from typing import Optional

from backend.models.order import Order, OrderItem
from backend.repositories.order_repository import OrderRepository
from backend.repositories.product_repository import ProductRepository
from backend.services.price_calculator import PriceCalculator

logger = logging.getLogger(__name__)


# Sipariş özeti — sigortalı kargo eşiği ve ücreti
SHIPPING_FREE_THRESHOLD = 50_000.0
SHIPPING_FEE            = 750.0


def calculate_shipping(subtotal: float) -> float:
    """50.000 TL altı → 750 TL sigortalı kargo, üstü → ücretsiz."""
    return 0.0 if subtotal >= SHIPPING_FREE_THRESHOLD else SHIPPING_FEE


_VALID_PAYMENT_METHODS = {"card", "transfer", "cod", "pickup"}


class OrderService:

    def __init__(
        self,
        order_repo:    OrderRepository,
        product_repo:  ProductRepository,
        price_calc:    PriceCalculator,
    ):
        self._orders   = order_repo
        self._products = product_repo
        self._calc     = price_calc

    # ── Müşteri ───────────────────────────────────────────────

    def create_order(
        self,
        user_id: int,
        cart: list[dict],       # [{"product_id": int, "quantity": int}, ...]
        gold_gram_price: float,
        notes: Optional[str] = None,
        payment_method: Optional[str] = None,
    ) -> Order:
        """
        Sepet içeriğinden sipariş oluşturur.
        Fiyatlar sipariş anındaki kura göre hesaplanır ve dondurulur.
        - payment_method: 'card' | 'transfer' | 'cod' | 'pickup' (None = belirtilmemiş)
        - Kargo/sigorta tutarı subtotal'a göre otomatik hesaplanır.
        - Benzersiz bir sipariş numarası (KJ-YYYY-NNNNN) atanır.
        """
        if payment_method is not None and payment_method not in _VALID_PAYMENT_METHODS:
            raise ValueError(f"Geçersiz ödeme yöntemi: {payment_method}")

        items: list[OrderItem] = []
        subtotal = 0.0

        for entry in cart:
            product = self._products.get_by_id(entry["product_id"])
            if product is None:
                raise ValueError(f"Ürün bulunamadı: id={entry['product_id']}")
            if not product.is_in_stock():
                raise ValueError(f"Stokta yok: {product.name}")

            qty        = int(entry["quantity"])
            unit_price = self._calc.calculate(product, gold_gram_price)
            subtotal  += unit_price * qty

            items.append(OrderItem(
                order_id=0,               # create() sonrası gerçek id atanır
                product_id=product.id,
                quantity=qty,
                unit_price=unit_price,
                gold_rate_at_order=gold_gram_price,
                product_name=product.name,
            ))

        shipping = calculate_shipping(subtotal)
        total    = round(subtotal + shipping, 2)

        # Havale/EFT seçildiyse "ödeme bekliyor" anlamında pending tut.
        # Diğer ödeme yöntemleri "Hazırlanıyor" gösterilir (yine pending status).
        # Mağazadan teslim → onaylandı kabul edilebilir (processing).
        status = "processing" if payment_method == "pickup" else "pending"

        order = Order(
            user_id=user_id,
            total_amount=total,
            shipping_amount=round(shipping, 2),
            payment_method=payment_method,
            order_number=self._generate_order_number(),
            status=status,
            notes=notes,
            items=items,
        )

        created = self._orders.create(order)
        if created is None:
            raise RuntimeError("Sipariş kaydedilemedi.")

        logger.info(
            "Sipariş oluşturuldu: %s id=%d user=%d toplam=%.2f kargo=%.2f ödeme=%s",
            created.order_number, created.id, user_id, total, shipping,
            payment_method or "—",
        )
        return created

    def _generate_order_number(self) -> str:
        """KJ-YYYY-NNNNN formatında benzersiz numara üretir (en fazla 20 deneme)."""
        year = datetime.now().year
        for _ in range(20):
            num = f"KJ-{year}-{random.randint(10000, 99999)}"
            if not self._orders.order_number_exists(num):
                return num
        # Pratik olarak buraya hiç düşmez; düşse de unique constraint tetiklenir.
        return f"KJ-{year}-{random.randint(100000, 999999)}"

    def get_user_orders(self, user_id: int) -> list[Order]:
        return self._orders.get_by_user(user_id)

    # ── Admin ─────────────────────────────────────────────────

    def get_all_orders(self) -> list[Order]:
        return self._orders.get_all()

    def update_status(
        self,
        order_id: int,
        status: str,
        admin_notes: Optional[str] = None,
    ) -> bool:
        allowed = {"pending", "processing", "completed", "cancelled"}
        if status not in allowed:
            raise ValueError(f"Geçersiz durum: {status}")
        return self._orders.update_status(order_id, status, admin_notes)

    def get_dashboard_counts(self) -> dict:
        return {
            "pending":    self._orders.count_by_status("pending"),
            "processing": self._orders.count_by_status("processing"),
            "completed":  self._orders.count_by_status("completed"),
            "cancelled":  self._orders.count_by_status("cancelled"),
        }

    def get_user_statistics(self, user_id: int) -> dict:
        """
        Kullanıcının sipariş/alışveriş özeti:
          {
            "order_count":       int,  # toplam sipariş sayısı
            "completed_count":   int,  # tamamlanan sipariş sayısı
            "cancelled_count":   int,
            "pending_count":     int,
            "total_spent":       float,  # sadece iptal edilmemiş siparişlerin toplamı
            "item_count":        int,   # toplam alınan ürün adedi
            "orders":            list[Order],  # geçmiş sipariş listesi (tümü)
          }
        """
        orders = self._orders.get_by_user(user_id)

        order_count     = len(orders)
        completed_count = sum(1 for o in orders if o.status == "completed")
        cancelled_count = sum(1 for o in orders if o.status == "cancelled")
        pending_count   = sum(1 for o in orders if o.status == "pending")
        total_spent     = sum(o.total_amount for o in orders if o.status != "cancelled")
        item_count      = sum(
            sum(it.quantity for it in o.items)
            for o in orders if o.status != "cancelled"
        )

        return {
            "order_count":     order_count,
            "completed_count": completed_count,
            "cancelled_count": cancelled_count,
            "pending_count":   pending_count,
            "total_spent":     round(total_spent, 2),
            "item_count":      item_count,
            "orders":          orders,
        }
