"""Farmer discussion feed backed by individually authenticated accounts."""
import requests
import streamlit as st

from utils.config import API_BASE_URL


def _request(method: str, path: str, *, payload: dict | None = None):
    token = st.session_state.get("community_access_token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.request(
        method, f"{API_BASE_URL}{path}", json=payload, headers=headers, timeout=20
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _error_message(exc: requests.RequestException) -> str:
    if exc.response is not None:
        try:
            detail = exc.response.json().get("detail")
            if isinstance(detail, str):
                return detail
        except (ValueError, AttributeError):
            pass
    return "The community service could not complete that request. Check the backend connection."


def render_community() -> None:
    st.title("Farmer community")
    st.write("Share practical experience, ask questions, and learn from other growers.")
    st.caption("Community roles are self-reported. Posts are peer experience, not official advice or verified recommendations.")

    if not st.session_state.get("community_access_token"):
        st.warning("Pilot accounts are not email-verified and farmer roles are self-reported. Avoid sharing private contact, financial, or household information.")
        sign_in, create_account = st.tabs(["Sign in", "Create an account"])
        with sign_in:
            with st.form("community_sign_in"):
                email = st.text_input("Email address", key="community_login_email")
                password = st.text_input("Password", type="password", key="community_login_password")
                submit = st.form_submit_button("Sign in", type="primary")
            if submit:
                try:
                    response = _request("POST", "/community/login", payload={"email": email, "password": password})
                    st.session_state["community_access_token"] = response["access_token"]
                    st.session_state["community_account"] = response.get("account", {})
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(_error_message(exc))
        with create_account:
            with st.form("community_register"):
                display_name = st.text_input("Name shown to other community members", max_chars=80)
                email = st.text_input("Email address", key="community_register_email")
                password = st.text_input("Password (at least 12 characters)", type="password", key="community_register_password")
                submit = st.form_submit_button("Create farmer account", type="primary")
            if submit:
                try:
                    response = _request("POST", "/community/register", payload={
                        "display_name": display_name, "email": email, "password": password,
                    })
                    st.session_state["community_access_token"] = response["access_token"]
                    st.session_state["community_account"] = response.get("account", {})
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(_error_message(exc))
        return

    account = st.session_state.get("community_account", {})
    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.text(f"Posting as {account.get('display_name', 'community member')} · Farmer account")
    with top_right:
        if st.button("Sign out", key="community_sign_out"):
            st.session_state.pop("community_access_token", None)
            st.session_state.pop("community_account", None)
            st.rerun()

    with st.expander("Share an update or question", expanded=False):
        with st.form("community_new_post", clear_on_submit=True):
            title = st.text_input("Topic", max_chars=140, placeholder="What are you seeing in your field?")
            body = st.text_area("Your experience or question", max_chars=5000, height=150)
            submit = st.form_submit_button("Publish to the community", type="primary")
        if submit:
            try:
                _request("POST", "/community/posts", payload={"title": title, "body": body})
                st.success("Your update has been posted.")
                st.rerun()
            except requests.RequestException as exc:
                st.error(_error_message(exc))

    try:
        posts = _request("GET", "/community/posts?limit=30")
    except requests.RequestException as exc:
        st.error(_error_message(exc))
        return

    if not posts:
        st.info("No discussions yet. Start the first one by sharing an observation or question.")
        return

    for post in posts:
        post_id = post.get("id")
        author = post.get("author") or {}
        with st.container(border=True):
            st.subheader(post.get("title", "Community update"))
            st.text(f"{author.get('display_name', 'Community member')} · {author.get('role', 'farmer')} · {post.get('created_at', '')}")
            st.text(post.get("body", ""))
            with st.expander("Read replies and join the discussion"):
                try:
                    comments = _request("GET", f"/community/posts/{post_id}/comments")
                except requests.RequestException as exc:
                    comments = []
                    st.error(_error_message(exc))
                for comment in comments:
                    comment_author = comment.get("author") or {}
                    st.text(f"{comment_author.get('display_name', 'Community member')} · {comment_author.get('role', 'farmer')}")
                    st.text(comment.get("body", ""))
                    st.divider()
                with st.form(f"community_comment_{post_id}", clear_on_submit=True):
                    reply = st.text_area("Add a reply", max_chars=1500, key=f"reply_{post_id}")
                    reply_submit = st.form_submit_button("Reply")
                if reply_submit:
                    try:
                        _request("POST", f"/community/posts/{post_id}/comments", payload={"body": reply})
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(_error_message(exc))
            if str(post.get("author_id")) != str(account.get("id")):
                with st.popover("Report content"):
                    with st.form(f"report_post_{post_id}"):
                        reason = st.text_input("Reason (required)", max_chars=500)
                        report = st.form_submit_button("Send to administrators")
                    if report:
                        try:
                            _request("POST", f"/community/posts/{post_id}/report", payload={"reason": reason})
                            st.success("Report sent for administrator review.")
                        except requests.RequestException as exc:
                            st.error(_error_message(exc))
