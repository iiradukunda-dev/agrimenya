import re


_E164 = re.compile(r"^\+[1-9][0-9]{7,14}$")


def normalize_phone(raw: str, default_cc: str = "250") -> str:
    value = re.sub(r"[\s().-]", "", str(raw or ""))
    if value.startswith("00"):
        value = "+" + value[2:]
    if value.startswith("+"):
        normalized = value
    elif value.startswith(default_cc) and value.isdigit():
        normalized = "+" + value
    elif value.startswith("0"):
        normalized = "+" + default_cc + value[1:]
    elif value.isdigit():
        normalized = "+" + default_cc + value
    else:
        raise ValueError("Phone number must contain digits and an optional leading +")

    if not _E164.fullmatch(normalized):
        raise ValueError("Phone number must be a valid E.164 number")
    if normalized.startswith("+250") and not re.fullmatch(r"\+2507[0-9]{8}", normalized):
        raise ValueError("Rwandan mobile numbers must start with +2507 and contain 12 digits")
    return normalized


def mask_phone(e164: str) -> str:
    if not _E164.fullmatch(e164 or ""):
        raise ValueError("Phone number must be a valid E.164 number")
    if e164.startswith("+250"):
        return "+250•••••" + e164[-3:]
    return e164[:4] + "•" * max(0, len(e164) - 7) + e164[-3:]
