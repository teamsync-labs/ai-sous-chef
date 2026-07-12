import logging
from logging.handlers import TimedRotatingFileHandler
import sys


def setup_logging(level: str = "INFO", log_file: str | None = None):
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(log_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []
    logger.addHandler(console_handler)

    if log_file:
        file_handler = TimedRotatingFileHandler(
            log_file,
            encoding="utf-8",
            when="midnight",
            backupCount=7)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
