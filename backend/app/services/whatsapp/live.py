from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.whatsapp.base import SendResult

logger = logging.getLogger(__name__)

# Verify these mappings against Meta's current error-code documentation.
META_ERROR_CODES = {
    "131047": ("outside_window", False),
    "131026": ("undeliverable", False),
    "131048": ("spam_rate_limit", False),
    "130429": ("throughput_limit", True),
    "131056": ("pair_rate_limit", True),
    "131049": ("not_delivered_for_ecosystem_health", False),
    "190": ("token_invalid", False),
}


class LiveProvider:
    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client

    async def _post(self, payload: dict[str, Any]) -> SendResult:
        url = (
            f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
            f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )
        headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
        timeout = httpx.Timeout(10.0, connect=5.0)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=timeout)
        try:
            for attempt in range(4):
                try:
                    response = await client.post(url, json=payload, headers=headers, timeout=timeout)
                except (httpx.TimeoutException, httpx.NetworkError):
                    if attempt == 3:
                        logger.warning("WhatsApp provider network failure after retries")
                        return SendResult(False, error_code="network_error", error_detail="Provider unavailable", retryable=True)
                    await asyncio.sleep(0.25 * (2 ** attempt))
                    continue

                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 3:
                        await asyncio.sleep(0.25 * (2 ** attempt))
                        continue
                    logger.warning("WhatsApp provider returned retryable HTTP %s", response.status_code)
                    return SendResult(False, error_code=f"http_{response.status_code}", error_detail="Provider temporarily unavailable", retryable=True)

                if not response.is_success:
                    data = _response_json(response)
                    error = data.get("error") or {}
                    code = str(error.get("code") or "provider_error")
                    mapped, retryable = META_ERROR_CODES.get(code, ("provider_error", False))
                    logger.info("WhatsApp provider rejected message (%s)", mapped)
                    return SendResult(False, error_code=code, error_detail=mapped, retryable=retryable)

                data = _response_json(response)
                messages = data.get("messages") or []
                message_id = messages[0].get("id") if messages and isinstance(messages[0], dict) else None
                return SendResult(True, wa_message_id=message_id)
        finally:
            if own_client:
                await client.aclose()
        return SendResult(False, error_code="provider_error", error_detail="Provider unavailable")

    async def send_text(self, to: str, body: str) -> SendResult:
        return await self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body, "preview_url": False},
        })

    async def send_template(
        self, to: str, template_name: str, language: str, params: list[str]
    ) -> SendResult:
        return await self._post({
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": value} for value in params],
                }],
            },
        })


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}
