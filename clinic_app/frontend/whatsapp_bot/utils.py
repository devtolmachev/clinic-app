from types import FunctionType
from typing import Any

from loguru import logger


def error_handler(f: FunctionType) -> Any:
    """Error handler."""

    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)

    return wrapper