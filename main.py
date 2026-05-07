"""
Kuyumcu Yönetim Sistemi — Uygulama Giriş Noktası

Başlatma sırası:
  1. Loglama yapılandırması
  2. AppContext (DB + tüm servisler)
  3. PyQt6 uygulaması
  4. Giriş penceresi
"""

import sys
import logging

from PyQt6.QtWidgets import QApplication

import config
from backend.utils.logger import setup_logging
from backend.app_context import AppContext
from frontend.styles.app_theme import global_style

logger = logging.getLogger(__name__)


def main() -> None:
    # ── Loglama ───────────────────────────────────────────────
    setup_logging(config.LOG_FILE, config.LOG_LEVEL)
    logger.info("=== %s v%s başlatılıyor ===", config.APP_NAME, config.APP_VERSION)

    # ── Backend Başlatma ──────────────────────────────────────
    ctx = AppContext(db_path=config.DB_PATH)

    # ── PyQt6 Uygulaması ──────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setStyleSheet(global_style())

    # ── Giriş Penceresi ───────────────────────────────────────
    # LoginWindow import'u burada — PyQt6 app oluşturulduktan sonra yapılır
    from frontend.windows.login_window import LoginWindow
    window = LoginWindow(ctx)
    window.show()

    exit_code = app.exec()

    # ── Temiz Çıkış ───────────────────────────────────────────
    ctx.shutdown()
    logger.info("Uygulama kapatıldı (exit_code=%d).", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
