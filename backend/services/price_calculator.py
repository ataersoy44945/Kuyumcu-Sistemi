"""
PriceCalculator — Ürün fiyat hesaplama iş mantığı.
UI veya başka servisler bu sınıfı kullanır; formül tek yerde yaşar.
"""

from backend.models.product import Product


class PriceCalculator:
    """
    Fiyat hesaplama motoru.

    Formül:
        altın_değeri  = gram × gram_altın_fiyatı × karat_katsayısı
        satış_fiyatı  = altın_değeri + işçilik + (altın_değeri × kar_marjı / 100)

    Eğer ürün use_calculated_price=False ise base_price doğrudan döner.
    """

    def calculate(self, product: Product, gold_gram_price: float) -> float:
        """
        Tek ürün için satış fiyatı hesaplar.

        Args:
            product: Fiyatı hesaplanacak ürün.
            gold_gram_price: Anlık gram altın fiyatı (TL).

        Returns:
            Satış fiyatı (TL), 2 ondalık basamakta yuvarlanmış.
        """
        if not product.use_calculated_price and product.base_price is not None:
            return round(product.base_price, 2)

        if gold_gram_price <= 0:
            return 0.0

        gold_value = product.weight_grams * gold_gram_price * product.karat_coefficient
        margin     = gold_value * product.profit_margin / 100
        total      = gold_value + product.labor_cost + margin
        return round(total, 2)
