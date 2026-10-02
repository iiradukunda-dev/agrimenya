import uuid
from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_no_llm_returns_context():
    zone_id = str(uuid.uuid4())
    payload = {"zone_id": zone_id, "question": "What's the score?"}

    with patch("app.db.crud.get_zone") as mock_get_zone, \
         patch("app.db.crud.list_predictions") as mock_preds, \
         patch("app.db.crud.get_alignment_metric") as mock_align, \
         patch("app.db.crud.list_alerts") as mock_alerts:
        mock_get_zone.return_value = {"id": zone_id, "district": "Gasabo", "sector": "S", "cell": "C"}
        mock_preds.return_value = []
        mock_align.return_value = None
        mock_alerts.return_value = []

        r = client.post("/chat", json=payload)
        assert r.status_code == 200
        assert "(No LLM configured yet" in r.json()["answer"]


def test_missing_zone_returns_404():
    zone_id = str(uuid.uuid4())
    payload = {"zone_id": zone_id, "question": "Q"}
    with patch("app.db.crud.get_zone") as mock_get_zone:
        mock_get_zone.return_value = None
        r = client.post("/chat", json=payload)
        assert r.status_code == 404
