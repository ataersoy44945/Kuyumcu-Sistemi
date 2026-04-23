"""
AppContext — Bağımlılık konteyneri (Dependency Injection).

Tüm repository ve servisler burada oluşturulur ve birbirine bağlanır.
main.py bu sınıfı bir kez başlatır; frontend pencerelerine geçirir.

Avantaj: Servisleri değiştirmek veya mock'lamak için tek bir yer.
"""

import logging
from pathlib import Path

from backend.database.database_manager import DatabaseManager
from backend.repositories.user_repository       import UserRepository
from backend.repositories.product_repository    import ProductRepository
from backend.repositories.category_repository   import CategoryRepository
from backend.repositories.favorite_repository   import FavoriteRepository
from backend.repositories.order_repository      import OrderRepository
from backend.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.repositories.campaign_repository   import CampaignRepository
from backend.api.exchange_rate_api              import ExchangeRateAPI
from backend.services.auth_service             import AuthService
from backend.services.product_service          import ProductService
from backend.services.favorite_service         import FavoriteService
from backend.services.order_service            import OrderService
from backend.services.price_calculator         import PriceCalculator
from backend.services.exchange_rate_service    import ExchangeRateService
from backend.services.campaign_service         import CampaignService
from backend.services.cart_service             import CartService

logger = logging.getLogger(__name__)


class AppContext:
    """
    Uygulama bağımlılık konteyneri.

    Kullanım:
        ctx = AppContext(db_path=config.DB_PATH)
        login_window = LoginWindow(ctx)
    """

    def __init__(self, db_path: Path):
        logger.info("AppContext başlatılıyor…")

        # ── Veritabanı ────────────────────────────────────────
        self.db   = DatabaseManager.initialize(db_path)
        conn      = self.db.get_connection()

        # ── Repositories ──────────────────────────────────────
        self.user_repo     = UserRepository(conn)
        self.product_repo  = ProductRepository(conn)
        self.category_repo = CategoryRepository(conn)
        self.favorite_repo = FavoriteRepository(conn)
        self.order_repo    = OrderRepository(conn)
        self.rate_repo     = ExchangeRateRepository(conn)
        self.campaign_repo = CampaignRepository(conn)

        # ── API Client ────────────────────────────────────────
        self.rate_api = ExchangeRateAPI()

        # ── Services ──────────────────────────────────────────
        self.auth_service     = AuthService(self.user_repo)
        self.product_service  = ProductService(self.product_repo, self.category_repo)
        self.favorite_service = FavoriteService(self.favorite_repo, self.product_repo)
        self.price_calculator = PriceCalculator()
        self.exchange_service = ExchangeRateService(self.rate_api, self.rate_repo)
        self.order_service    = OrderService(
            self.order_repo, self.product_repo, self.price_calculator
        )
        self.campaign_service = CampaignService(self.campaign_repo)
        self.cart_service     = CartService(conn)

        self._ensure_default_admin()
        logger.info("AppContext hazır.")

    def _ensure_default_admin(self) -> None:
        conn = self.db.get_connection()
        count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        if count == 0:
            self.auth_service.register_admin(
                username="admin", email="admin@kuyumcu.com",
                password="admin123", first_name="Sistem", last_name="Admin",
            )
            logger.info("Varsayılan admin oluşturuldu → kullanici: admin | sifre: admin123")

    def shutdown(self) -> None:
        """Uygulama kapanırken temiz bir çıkış sağlar."""
        self.db.close()
        logger.info("AppContext kapatıldı.")
