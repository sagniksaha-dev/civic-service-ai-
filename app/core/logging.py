import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured console logging for the application."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Custom log format with timestamp, level, logger name, and message
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    logger_instance = logging.getLogger("civic_ai")
    logger_instance.setLevel(log_level)
    return logger_instance


logger = setup_logging()
