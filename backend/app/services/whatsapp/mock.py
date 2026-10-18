from __future__ import annotations

from uuid import uuid4

from app.services.whatsapp.base import SendResult


class MockProvider:
    def __init__(self):
        self.sent: list[dict] = []
        self.failures: dict[str, SendResult] = {}
        self.status_events: list[dict] = []

    async def send_text(self, to: str, body: str) -> SendResult:
        failure = self.failures.get(to)
        if failure:
            return failure
        message_id = f"wamid.mock.{uuid4().hex}"
        self.sent.append({"to": to, "type": "text", "body": body, "id": message_id})
        return SendResult(True, wa_message_id=message_id)

    async def send_template(
        self, to: str, template_name: str, language: str, params: list[str]
    ) -> SendResult:
        failure = self.failures.get(to)
        if failure:
            return failure
        message_id = f"wamid.mock.{uuid4().hex}"
        self.sent.append({
            "to": to,
            "type": "template",
            "template_name": template_name,
            "language": language,
            "params": list(params),
            "id": message_id,
        })
        return SendResult(True, wa_message_id=message_id)

    def fail_for(self, to: str, result: SendResult) -> None:
        self.failures[to] = result

    def emit_status(self, message_id: str, status: str) -> dict:
        event = {"id": message_id, "status": status}
        self.status_events.append(event)
        return event
