"""
Logging para arquivo (logs/robo_sisab_AAAA-MM-DD.log) e console.
"""
import logging
import sys
from datetime import datetime

from . import config


def get_logger(name: str = "robo_sisab") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # evita handlers duplicados em re-imports
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Arquivo
    arquivo = config.LOG_DIR / f"robo_sisab_{datetime.now():%Y-%m-%d}.log"
    fh = logging.FileHandler(arquivo, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger
