import re


def format_phone(phone: str) -> str:
    """Format phone by RE and return it.

    Parameters
    ----------
    phone : str
        source phone string.

    Returns
    -------
    str
        formatted phone.
    """
    phone = re.sub(r"[\(\)]", r"", phone)

    pattern = r"\+*(7|8)\-*(\d{3})\-*(\d{3})\-*(\d{2})\-*(\d{2})"
    if not re.findall(pattern, phone):
        return

    return re.sub(
        r"\+*(7|8)\-*(\d{3})\-*(\d{3})\-*(\d{2})\-*(\d{2})",
        r"7-\2-\3-\4-\5",
        phone,
    )

