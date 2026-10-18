from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SendResult:
    ok: bool
    wa_message_id: str | None = None
    error_code: str | None = None
    error_detail: str | None = None
    retryable: bool = False


class WhatsAppProvider(Protocol):
    async def send_text(self, to: str, body: str) -> SendResult: ...

    async def send_template(
        self, to: str, template_name: str, language: str, params: list[str]
    ) -> SendResult: ...
