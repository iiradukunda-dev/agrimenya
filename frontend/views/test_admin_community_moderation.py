from views.admin import _community_report_target_id


def test_admin_moderation_resolves_reported_target_for_each_content_type():
    assert _community_report_target_id(
        {"post_id": "post-id"}, "post",
    ) == "post-id"
    assert _community_report_target_id(
        {"comment_id": "comment-id"}, "comment",
    ) == "comment-id"
    assert _community_report_target_id(
        {"field_report_id": "field-report-id"}, "field_report",
    ) == "field-report-id"
