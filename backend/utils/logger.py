"""
Merkezi loglama yapılandırması.
main.py başlarken setup_logging() çağrılır; sonrası logging.getLogger() ile kullanılır.
"""

import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_file: Path, level: str = "INFO") -> None:
    """
    Uygulama geneli loglama ayarlarını yapar.
    - Dosyaya dönen log (günlük rotasyon)
    - Konsol çıktısı

    Args:
        log_file: Log dosyasının tam yolu.
        level: Loglama seviyesi string olarak ("DEBUG", "INFO", "WARNING", "ERROR").
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Günlük log dosyası (7 gün sakla)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Konsol handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
