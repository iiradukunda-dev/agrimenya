import re


_STOP_WORDS = {"STOP", "STOPPED", "UNSUBSCRIBE", "HEREZA", "SHIRA"}
_START_WORDS = {"START", "JOIN", "EMERA"}


def parse_keyword(text: str) -> str | None:
    normalized = re.sub(r"[^\w]+", " ", str(text or "").upper(), flags=re.UNICODE).strip()
    if not normalized:
        return None
    if normalized in _STOP_WORDS:
        return "STOP"
    if normalized in _START_WORDS:
        return "START"
    return None
