import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch('app.db.crud.get_zone')
@patch('app.db.crud.update_plan')
@patch('app.db.crud.delete_plan')
@patch('app.db.crud.list_plans')
@patch('app.db.crud.list_alerts')
@patch('app.db.crud.update_alert')
@patch('app.db.crud.delete_alert')
def test_admin_plan_and_alert_crud(
    mock_delete_alert,
    mock_update_alert,
    mock_list_alerts,
    mock_list_plans,
    mock_delete_plan,
    mock_update_plan,
    mock_get_zone,
):
    plan_id = str(uuid.uuid4())
    alert_id = str(uuid.uuid4())
    zone_id = str(uuid.uuid4())

    mock_get_zone.return_value = {'id': zone_id, 'district': 'Gasabo'}
    mock_list_plans.return_value = [{'id': plan_id, 'zone_id': zone_id, 'title': 'Plan A'}]
    mock_list_alerts.return_value = [{'id': alert_id, 'zone_id': zone_id, 'message': 'Issue'}]
    mock_update_plan.return_value = {'id': plan_id, 'title': 'Updated'}
    mock_update_alert.return_value = {'id': alert_id, 'message': 'Updated alert'}
    mock_delete_plan.return_value = {'id': plan_id, 'deleted': True}
    mock_delete_alert.return_value = {'id': alert_id, 'deleted': True}

    headers = {'X-Admin-Key': 'secret-key'}
    import app.core.config as config
    config.settings.ADMIN_API_KEY = 'secret-key'

    plans = client.get('/admin/plans', headers=headers)
    assert plans.status_code == 200

    update_plan = client.patch(f'/admin/plans/{plan_id}', json={'title': 'Updated'}, headers=headers)
    assert update_plan.status_code == 200

    delete_plan = client.delete(f'/admin/plans/{plan_id}', headers=headers)
    assert delete_plan.status_code == 200

    alerts = client.get('/admin/alerts', headers=headers)
    assert alerts.status_code == 200

    update_alert = client.patch(f'/admin/alerts/{alert_id}', json={'message': 'Updated alert'}, headers=headers)
    assert update_alert.status_code == 200

    delete_alert = client.delete(f'/admin/alerts/{alert_id}', headers=headers)
    assert delete_alert.status_code == 200
