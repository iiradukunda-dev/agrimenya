from functools import lru_cache

from app.core.config import settings
from app.services.whatsapp.base import SendResult, WhatsAppProvider


@lru_cache(maxsize=1)
def get_provider() -> WhatsAppProvider:
    if settings.WHATSAPP_MODE == "mock":
        from app.services.whatsapp.mock import MockProvider

        return MockProvider()
    from app.services.whatsapp.live import LiveProvider

    return LiveProvider()


def reset_provider() -> None:
    get_provider.cache_clear()


__all__ = ["SendResult", "WhatsAppProvider", "get_provider", "reset_provider"]
