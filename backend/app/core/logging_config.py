from __future__ import annotations

import logging
from logging.config import dictConfig

from app.core.config import settings


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": settings.LOG_LEVEL,
                }
            },
            "root": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
            },
        }
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
