import logging
import os
from logging.handlers import RotatingFileHandler
from config.settings import LOG_LEVEL, BOT_NAME

logger = logging.getLogger(BOT_NAME)


def start():
    log_dir = f"logs/{BOT_NAME}"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = f"{BOT_NAME}.log"
    log_filepath = os.path.join(log_dir, log_filename)

    logger.setLevel(LOG_LEVEL)

    handler = RotatingFileHandler(
        log_filepath, maxBytes=6 * 1024 * 1024, backupCount=6, encoding="utf-16"
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
