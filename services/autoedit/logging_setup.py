from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("autoedit")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
