from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.core.auth import create_token
from app.core.config import settings
from app.db import crud
from app.main import app

client = TestClient(app)
COMMUNITY_ID = "00000000-0000-4000-8000-000000000101"
OTHER_ID = "00000000-0000-4000-8000-000000000102"
POST_ID = "00000000-0000-4000-8000-000000000103"
REPORT_ID = "00000000-0000-4000-8000-000000000104"
FIELD_REPORT_ID = "00000000-0000-4000-8000-000000000105"


def community_headers(monkeypatch) -> dict[str, str]:
    monkeypatch.setattr(settings, "APP_ENV", "test")
    monkeypatch.setattr(settings, "JWT_SECRET", "test-community-secret-that-is-at-least-32-chars")
    monkeypatch.setattr(crud, "get_community_account_by_id", lambda _: {
        "id": COMMUNITY_ID,
        "display_name": "test_farmer",
        "role": "farmer",
        "is_active": True,
        "session_version": 1,
    })
    token = create_token("community", claims={"sub": COMMUNITY_ID, "ver": 1})
    return {"Authorization": f"Bearer {token}"}


def test_community_profile_update_validates_and_saves_username(monkeypatch):
    headers = community_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_account_by_username", lambda _: None)
    update = Mock(return_value={
        "id": COMMUNITY_ID, "display_name": "new_farmer", "role": "farmer",
    })
    monkeypatch.setattr(crud, "update_community_account_display_name", update)

    response = client.patch(
        "/community/profile", json={"display_name": "New_Farmer"}, headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["account"]["display_name"] == "new_farmer"
    update.assert_called_once_with(COMMUNITY_ID, "new_farmer")

    invalid = client.patch(
        "/community/profile", json={"display_name": "bad name"}, headers=headers,
    )
    assert invalid.status_code == 422


def test_community_profile_update_rejects_an_existing_username(monkeypatch):
    headers = community_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_account_by_username", lambda _: {
        "id": OTHER_ID, "display_name": "taken_name",
    })
    update = Mock()
    monkeypatch.setattr(crud, "update_community_account_display_name", update)

    response = client.patch(
        "/community/profile", json={"display_name": "taken_name"}, headers=headers,
    )

    assert response.status_code == 409
    update.assert_not_called()


def test_community_field_report_filters_are_bounded_and_passed_to_crud(monkeypatch):
    headers = community_headers(monkeypatch)
    list_reports = Mock(return_value=[])
    monkeypatch.setattr(crud, "list_community_field_reports", list_reports)

    response = client.get(
        "/community/field-reports?limit=5&offset=20&district=Gasabo&crop=Maize",
        headers=headers,
    )

    assert response.status_code == 200
    list_reports.assert_called_once_with(
        5, 20, district="Gasabo", crop="Maize",
    )
    invalid = client.get(
        "/community/field-reports?limit=21", headers=headers,
    )
    assert invalid.status_code == 422


def test_community_notifications_are_scoped_to_the_signed_in_account(monkeypatch):
    headers = community_headers(monkeypatch)
    list_notifications = Mock(return_value=[{"id": "notification-id"}])
    mark_read = Mock(return_value=1)
    monkeypatch.setattr(crud, "list_community_notifications", list_notifications)
    monkeypatch.setattr(crud, "mark_community_notifications_read", mark_read)

    response = client.get("/community/notifications", headers=headers)
    marked = client.post("/community/notifications/read", headers=headers)

    assert response.status_code == 200
    assert response.json() == [{"id": "notification-id"}]
    list_notifications.assert_called_once_with(COMMUNITY_ID, 10)
    assert marked.status_code == 200
    assert marked.json() == {"marked_read": 1}
    mark_read.assert_called_once_with(COMMUNITY_ID)


def test_field_observation_owner_cannot_report_own_observation(monkeypatch):
    headers = community_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_field_report", lambda _: {
        "id": FIELD_REPORT_ID, "reporter_id": COMMUNITY_ID,
    })
    create_report = Mock()
    monkeypatch.setattr(crud, "create_community_report", create_report)

    response = client.post(
        f"/community/field-reports/{FIELD_REPORT_ID}/report",
        json={"reason": "This observation is misleading"},
        headers=headers,
    )

    assert response.status_code == 400
    create_report.assert_not_called()


def test_member_can_report_another_members_field_observation(monkeypatch):
    headers = community_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_field_report", lambda _: {
        "id": FIELD_REPORT_ID, "reporter_id": OTHER_ID,
    })
    create_report = Mock(return_value={"id": REPORT_ID, "field_report_id": FIELD_REPORT_ID})
    monkeypatch.setattr(crud, "create_community_report", create_report)

    response = client.post(
        f"/community/field-reports/{FIELD_REPORT_ID}/report",
        json={"reason": "This observation has no supporting details"},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["field_report_id"] == FIELD_REPORT_ID
    create_report.assert_called_once_with(
        COMMUNITY_ID, reason="This observation has no supporting details",
        field_report_id=FIELD_REPORT_ID,
    )


def test_moderation_rejects_a_report_for_different_content(monkeypatch):
    from tests.auth_helpers import admin_headers

    headers = admin_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_report", lambda _: {
        "id": REPORT_ID, "status": "open", "post_id": POST_ID,
        "comment_id": None, "field_report_id": None,
    })
    moderate = Mock(return_value=True)
    monkeypatch.setattr(crud, "moderate_community_content", moderate)

    response = client.patch(
        "/community/moderation",
        json={
            "target_kind": "post",
            "target_id": FIELD_REPORT_ID,
            "action": "hide",
            "report_id": REPORT_ID,
        },
        headers=headers,
    )

    assert response.status_code == 400
    moderate.assert_not_called()


def test_field_observation_report_can_be_dismissed(monkeypatch):
    from tests.auth_helpers import admin_headers
    from app.routers import community

    headers = admin_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_report", lambda _: {
        "id": REPORT_ID, "status": "open", "post_id": None,
        "comment_id": None, "field_report_id": FIELD_REPORT_ID,
    })
    resolve = Mock(return_value=True)
    monkeypatch.setattr(crud, "resolve_community_report", resolve)
    monkeypatch.setattr(community, "audit_admin_action", Mock())

    response = client.patch(
        "/community/moderation",
        json={
            "target_kind": "field_report",
            "target_id": FIELD_REPORT_ID,
            "action": "dismiss",
            "report_id": REPORT_ID,
            "report_action": "dismissed",
        },
        headers=headers,
    )

    assert response.status_code == 200
    resolve.assert_called_once_with(REPORT_ID, "00000000-0000-4000-8000-000000000001", "dismissed")


def test_deleting_a_reported_field_observation_removes_its_photo_record(monkeypatch):
    from tests.auth_helpers import admin_headers
    from app.routers import community

    headers = admin_headers(monkeypatch)
    monkeypatch.setattr(crud, "get_community_report", lambda _: {
        "id": REPORT_ID, "status": "open", "post_id": None,
        "comment_id": None, "field_report_id": FIELD_REPORT_ID,
    })
    delete_report = Mock(return_value={"id": FIELD_REPORT_ID, "photo_path": None})
    resolve = Mock()
    monkeypatch.setattr(crud, "delete_community_field_report", delete_report)
    monkeypatch.setattr(crud, "resolve_community_report", resolve)
    monkeypatch.setattr(community, "audit_admin_action", Mock())

    response = client.patch(
        "/community/moderation",
        json={
            "target_kind": "field_report",
            "target_id": FIELD_REPORT_ID,
            "action": "delete",
            "report_id": REPORT_ID,
        },
        headers=headers,
    )

    assert response.status_code == 200
    delete_report.assert_called_once_with(FIELD_REPORT_ID)
    resolve.assert_not_called()
