import re
from typing import Optional


def format_phone(phone: str) -> Optional[str]:
    """Format phone by RE and return it.

    Parameters
    ----------
    phone : str
        source phone string.

    Returns
    -------
    Optional[str]
        formatted phone.
    """
    phone = re.sub(r"[\(\)]", r"", phone)

    pattern = r"\+*(7|8)\-*(\d{3})\-*(\d{3})\-*(\d{2})\-*(\d{2})"
    phone_raw = re.findall(pattern, phone)
    if not phone_raw:
        return

    return re.sub(pattern, r"\1-(\2)-\3-\4-\5", phone)
