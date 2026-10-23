"""Farmer discussion feed backed by individually authenticated accounts."""
import requests
import streamlit as st
import time
from datetime import date
from io import BytesIO
from PIL import Image

from utils.config import API_BASE_URL
from utils.i18n import get_current_language

COPY = {
    "en": {
        "title": "Farmer community", "intro": "Share practical experience, ask questions, and learn from other growers.",
        "wa_title": "Use Agri-Menya on WhatsApp",
        "wa_intro": "Open a chat to access district crop evidence and alert tools without signing in to the website.",
        "wa_commands": "Send HELP for the menu. Try DISTRICT <name>, RANK <crop>, SUBSCRIBE <district> [crop], STATUS, ALERTS, or LANG RW. Reply START only if you want WhatsApp alerts; STOP opts out.",
        "wa_pending": "WhatsApp chat is not enabled for users yet. The website services remain available here.",
        "wa_unavailable": "WhatsApp availability could not be checked. You can continue using the website.",
        "wa_open": "Open Agri-Menya WhatsApp chat",
        "language": "Language / Ururimi", "warning": "Farmer observations are community reports, not official NISR statistics or verified agronomic advice.",
        "reports": "Field observations", "report_help": "A short field note can help others understand what is happening locally.",
        "district": "District / field location", "crop": "Crop", "date": "Date observed", "symptoms": "What did you notice? (optional)",
        "notes": "Extra details (optional)", "photo": "Photo (optional, compressed before upload)", "save_report": "Share field observation",
        "saved": "Observation shared.", "no_reports": "No field observations yet.", "unknown_author": "Community member",
        "signin": "Sign in", "create": "Create account", "email": "Email address", "password": "Password",
        "name": "Username (3–30 letters, numbers, or underscores)", "create_farmer": "Create farmer account", "signout": "Sign out",
        "new_post": "What’s happening on your farm or in your community?", "topic": "Add a short topic (optional)", "post_body": "Share an update or ask the community",
        "publish": "Publish to the community", "posted": "Your update has been posted.", "replies": "Read replies and join the discussion",
        "reply": "Add a reply", "send_reply": "Reply", "report": "Report content", "reason": "Reason (required)",
        "send_report": "Send to administrators", "report_sent": "Report sent for administrator review.",
        "privacy": "Pilot accounts are not email-verified. Avoid sharing private contact, financial, or household information.",
        "account_name": "Posting as", "farmer": "Farmer account", "empty": "No discussions yet. Start the first one by sharing an observation or question.",
        "unavailable": "District choices are unavailable. Check your connection and try again.", "crop_required": "Enter the crop name.",
        "valid_photo": "Choose a valid photo.", "photo_too_large": "Photo is still too large. Choose a smaller image.",
        "farmer_observation": "Farmer observation", "photo_caption": "Farmer-submitted photo",
        "posting_as": "Posting as", "reply_author": "Community member", "role_farmer": "farmer",
        "delete_post": "Delete my post", "delete_confirm": "Delete this post? This cannot be undone.",
        "post_deleted": "Your post was deleted.",
        "discussion_tab": "Discussions", "field_tab": "Field observations", "reply_count": "Replies",
        "delete_observation": "Delete my observation", "observation_deleted": "Field observation deleted.",
        "observation_delete_confirm": "Delete this field observation and its photo? This cannot be undone.",
        "forgot_password": "Forgot your password?", "send_reset": "Send reset link",
        "reset_password": "Choose a new password", "confirm_password": "Confirm new password",
        "save_password": "Update password", "reset_requested": "If an account matches that email, a reset link will arrive shortly.",
        "reset_dev_link": "Open the one-time password reset link",
        "reset_dev_error": "Could not create the reset link. Confirm the backend can reach the database.",
        "password_updated": "Password updated. Sign in with your new password.", "password_mismatch": "The passwords do not match.",
    },
    "rw": {
        "title": "Umuryango w'abahinzi", "intro": "Sangiza abandi ubunararibonye, ubaze ibibazo kandi wungurane ubumenyi.",
        "wa_title": "Koresha Agri-Menya kuri WhatsApp",
        "wa_intro": "Fungura ikiganiro kugira ngo ubone imibare y'ibihingwa mu turere n'ibikoresho by'amatangazo, utabanje kwinjira ku rubuga.",
        "wa_commands": "Ohereza HELP kugira ngo ubone amabwiriza. Gerageza DISTRICT <akarere>, RANK <igihingwa>, SUBSCRIBE <akarere> [igihingwa], STATUS, ALERTS cyangwa LANG RW. Ohereza EMERA gusa niba ushaka kwakira amatangazo kuri WhatsApp; SHIRA ihagarika amatangazo.",
        "wa_pending": "Ikiganiro cya WhatsApp ntikirafungurirwa abakoresha. Ushobora gukomeza gukoresha serivisi zo ku rubuga.",
        "wa_unavailable": "Ntibyashobotse kugenzura WhatsApp. Ushobora gukomeza gukoresha urubuga.",
        "wa_open": "Fungura ikiganiro cya Agri-Menya kuri WhatsApp",
        "language": "Language / Ururimi", "warning": "Ibyo abahinzi batangaje ni amakuru y'umuryango gusa; si imibare yemewe ya NISR cyangwa inama zemejwe.",
        "reports": "Amakuru yo mu murima", "report_help": "Andika muri make ibyo wabonye kugira ngo bifashe abandi kumenya uko umurima umeze.",
        "district": "Akarere / aho umurima uherereye", "crop": "Igihingwa", "date": "Itariki waboneyeho", "symptoms": "Wabonye iki? (si ngombwa)",
        "notes": "Ibindi bisobanuro (si ngombwa)", "photo": "Ifoto (si ngombwa; iragabanywa mbere yo koherezwa)", "save_report": "Sangiza amakuru yo mu murima",
        "saved": "Amakuru yo mu murima yasangijwe.", "no_reports": "Nta makuru yo mu murima arahari.", "unknown_author": "Umunyamuryango",
        "signin": "Injira", "create": "Fungura konti", "email": "Imeyili", "password": "Ijambo ry'ibanga",
        "name": "Izina ukoresha (inyuguti, imibare cyangwa _; 3–30)", "create_farmer": "Fungura konti y'umuhinzi", "signout": "Sohoka",
        "new_post": "Ni iki kiri kubera mu murima cyangwa mu muryango?", "topic": "Ongeraho umutwe mugufi (si ngombwa)", "post_body": "Sangiza amakuru cyangwa ubaze umuryango",
        "publish": "Sangiza umuryango", "posted": "Amakuru yawe yasangijwe.", "replies": "Soma ibisubizo unaganire n'abandi",
        "reply": "Andika igisubizo", "send_reply": "Subiza", "report": "Tanga ikirego", "reason": "Impamvu (ni ngombwa)",
        "send_report": "Ohereza ku bayobozi", "report_sent": "Ikirego cyoherejwe ku bayobozi.",
        "privacy": "Konti z'igerageza ntizigenzura imeyili. Irinde gushyiraho telefoni, amafaranga cyangwa amakuru y'urugo.",
        "account_name": "Urasangiza nka", "farmer": "Konti y'umuhinzi", "empty": "Nta biganiro birimo. Tangiza ikiganiro usangiza abandi ibyo wabonye cyangwa ikibazo.",
        "unavailable": "Akarere ntikabonetse. Reba interineti wongere ugerageze.", "crop_required": "Andika izina ry'igihingwa.",
        "valid_photo": "Hitamo ifoto yemewe.", "photo_too_large": "Ifoto iracyaremereye. Hitamo ntoya.",
        "farmer_observation": "Amakuru yatanzwe n'umuhinzi", "photo_caption": "Ifoto yatanzwe n'umuhinzi",
        "posting_as": "Urasangiza nka", "reply_author": "Umunyamuryango", "role_farmer": "umuhinzi",
        "delete_post": "Siba inyandiko yanjye", "delete_confirm": "Urifuza gusiba iyi nyandiko? Ntibisubirwaho.",
        "post_deleted": "Inyandiko yawe yasibwe.",
        "discussion_tab": "Ibiganiro", "field_tab": "Amakuru yo mu murima", "reply_count": "Ibisubizo",
        "delete_observation": "Siba amakuru yanjye", "observation_deleted": "Amakuru yo mu murima yasibwe.",
        "observation_delete_confirm": "Urifuza gusiba aya makuru n'ifoto yayo? Ntibisubirwaho.",
        "forgot_password": "Wibagiwe ijambo ry'ibanga?", "send_reset": "Ohereza umurongo wo guhindura",
        "reset_password": "Shyiraho ijambo ry'ibanga rishya", "confirm_password": "Ongera wandike ijambo ry'ibanga",
        "save_password": "Hindura ijambo ry'ibanga", "reset_requested": "Niba iyi imeyili ifite konti, umurongo wo guhindura uraza koherezwa.",
        "reset_dev_link": "Fungura umurongo wo guhindura ijambo ry'ibanga",
        "reset_dev_error": "Ntibyashobotse gukora umurongo. Reba ko backend ishobora kugera kuri database.",
        "password_updated": "Ijambo ry'ibanga ryahinduwe. Injira ukoresheje irishya.", "password_mismatch": "Amagambo y'ibanga ntahura.",
    },
}


@st.cache_data(ttl=600, show_spinner=False)
def _district_zones() -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/segmentation/zones", timeout=8)
    response.raise_for_status()
    return response.json()


def _field_reports(token: str, language: str) -> None:
    c = COPY[language]
    st.subheader(c["reports"])
    st.caption(c["warning"])
    try:
        zones = _district_zones()
    except requests.RequestException:
        zones = []
        st.info(c["unavailable"])
    zones = [item for item in zones if item.get("id")]
    if zones:
        zone_by_label = {}
        for item in zones:
            if not item.get("id"):
                continue
            parts = [item.get("district"), item.get("sector") or item.get("cell")]
            location = " / ".join(str(part) for part in parts if part)
            label = f"{location or 'Location not recorded'} · {str(item['id'])[-8:]}"
            zone_by_label[label] = item
        with st.expander(c["report_help"], expanded=False):
            st.caption("Add a location, crop, date, and a brief note. A photo is optional; reports remain community observations, not verified diagnoses.")
            with st.form("community_field_observation", clear_on_submit=True):
                selected_zone_label = st.selectbox(c["district"], list(zone_by_label))
                crop = st.text_input(c["crop"], max_chars=50, placeholder="e.g. Maize / Ibigori")
                observed_on = st.date_input(c["date"], value=date.today())
                symptoms = st.text_area(c["symptoms"], max_chars=500, height=110, placeholder="Describe what you saw, where it appears, and when it started.")
                notes = st.text_area(c["notes"], max_chars=1000, height=90)
                photo = st.file_uploader(c["photo"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=False)
                submit = st.form_submit_button(c["save_report"], type="primary", use_container_width=True)
            if submit:
                zone = zone_by_label.get(selected_zone_label)
                if not crop.strip():
                    st.error(c["crop_required"])
                else:
                    files = None
                    if photo is not None:
                        try:
                            image = Image.open(photo).convert("RGB")
                            image.thumbnail((1400, 1400))
                            compressed = BytesIO()
                            image.save(compressed, format="JPEG", quality=72, optimize=True)
                            if len(compressed.getvalue()) > 5 * 1024 * 1024:
                                raise ValueError(c["photo_too_large"])
                            files = {"photo": ("field.jpg", compressed.getvalue(), "image/jpeg")}
                        except (OSError, ValueError) as exc:
                            st.error(str(exc) or c["valid_photo"])
                    if photo is None or files:
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/community/field-reports",
                                data={"zone_id": zone["id"], "crop": crop.strip(), "observed_on": observed_on.isoformat(),
                                      "symptoms": symptoms.strip(), "notes": notes.strip()},
                                files=files, headers={"Authorization": f"Bearer {token}"}, timeout=25,
                            )
                            response.raise_for_status()
                            st.success(c["saved"])
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc))
    try:
        response = requests.get(f"{API_BASE_URL}/community/field-reports?limit=10", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        response.raise_for_status()
        reports = response.json()
    except requests.RequestException as exc:
        st.error(_error_message(exc))
        return
    if not reports:
        st.caption(c["no_reports"])
    for report in reports:
        reporter = report.get("reporter") or {}
        author = reporter.get("display_name") or c["unknown_author"]
        zone = report.get("zone") or {}
        with st.container(border=True):
            st.markdown(f"**{report.get('crop', '')} · {report.get('district') or zone.get('district', '')}**")
            st.caption(f"{report.get('observed_on', '')} · {author} · {c['farmer_observation']}")
            if report.get("symptoms"):
                st.write(report["symptoms"])
            if report.get("notes"):
                st.caption(report["notes"])
            if report.get("photo_url"):
                st.caption(c["photo_caption"])
                st.image(report["photo_url"], width=360)
            account = st.session_state.get("community_account") or {}
            if str(reporter.get("id")) == str(account.get("id")):
                with st.popover(c["delete_observation"]):
                    st.warning(c["observation_delete_confirm"])
                    if st.button(c["delete_observation"], key=f"delete_field_report_{report.get('id')}", type="primary"):
                        try:
                            response = requests.delete(
                                f"{API_BASE_URL}/community/field-reports/{report['id']}",
                                headers={"Authorization": f"Bearer {token}"}, timeout=20,
                            )
                            response.raise_for_status()
                            st.success(c["observation_deleted"])
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))


def _request(method: str, path: str, *, payload: dict | None = None):
    token = st.session_state.get("community_access_token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.request(
        method, f"{API_BASE_URL}{path}", json=payload, headers=headers, timeout=20
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _store_community_session(response: dict) -> None:
    st.session_state["community_access_token"] = response["access_token"]
    st.session_state["community_access_token_expires_at"] = time.time() + int(response.get("expires_in", 3600))
    st.session_state["community_account"] = response.get("account", {})


def _clear_community_session(*, expired: bool = False) -> None:
    st.session_state.pop("community_access_token", None)
    st.session_state.pop("community_access_token_expires_at", None)
    st.session_state.pop("community_account", None)
    if expired:
        st.session_state["community_session_expired"] = True


def _error_message(exc: requests.RequestException, language: str = "en") -> str:
    if exc.response is not None:
        try:
            detail = exc.response.json().get("detail")
            if isinstance(detail, str):
                return detail
            if isinstance(detail, list):
                locations = {str(item.get("loc", [""])[-1]): item.get("type", "") for item in detail if isinstance(item, dict)}
                if "password" in locations:
                    return ("Password must be at least 12 characters." if language == "en"
                            else "Ijambo ry'ibanga rigomba kugira inyuguti nibura 12.")
                if "display_name" in locations:
                    return ("Use a username of 3–30 letters, numbers, or underscores." if language == "en"
                            else "Koresha izina rigizwe n'inyuguti, imibare cyangwa _, hagati ya 3 na 30.")
                if "email" in locations:
                    return ("Enter a valid email address." if language == "en"
                            else "Andika imeyili yemewe.")
                messages = [str(item.get("msg", "")) for item in detail if isinstance(item, dict) and item.get("msg")]
                if messages:
                    return " ".join(messages)
        except (ValueError, AttributeError):
            pass
    return "The community service could not complete that request. Check the backend connection."


def render_community() -> None:
    st.markdown('''<style>@media(max-width:700px){.block-container{padding:1rem .8rem 3rem!important}[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button{min-height:3rem;width:100%}[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{font-size:16px}}</style>''', unsafe_allow_html=True)
    language = get_current_language()
    c = COPY[language]
    st.title(c["title"])
    st.write(c["intro"])
    st.caption(c["warning"])

    try:
        whatsapp_info = requests.get(f"{API_BASE_URL}/communication/whatsapp-info", timeout=5)
        whatsapp_info.raise_for_status()
        whatsapp_info = whatsapp_info.json()
    except requests.RequestException:
        whatsapp_info = None
    with st.container(border=True):
        st.subheader(c["wa_title"])
        st.write(c["wa_intro"])
        if whatsapp_info and whatsapp_info.get("available") and whatsapp_info.get("chat_url"):
            st.link_button(c["wa_open"], whatsapp_info["chat_url"], type="primary")
            st.caption(c["wa_commands"])
        elif whatsapp_info is None:
            st.info(c["wa_unavailable"])
        else:
            st.info(c["wa_pending"])

    reset_token = st.query_params.get("community_reset_token")
    if reset_token:
        st.markdown("<style>.st-key-community_reset_panel{max-width:620px;margin:1.5rem auto}</style>", unsafe_allow_html=True)
        with st.container(key="community_reset_panel", border=True):
            st.subheader(c["reset_password"])
            st.caption("Use at least 12 characters. The reset link can be used once and expires after 30 minutes." if language == "en" else "Koresha inyuguti nibura 12. Umurongo ukoreshwa rimwe kandi urangira nyuma y'iminota 30.")
            with st.form("community_password_reset_form"):
                new_password = st.text_input(c["reset_password"], type="password", key="community_new_password")
                confirmation = st.text_input(c["confirm_password"], type="password", key="community_confirm_password")
                submit_reset = st.form_submit_button(c["save_password"], type="primary", use_container_width=True)
            if submit_reset:
                if len(new_password) < 12:
                    st.error("Password must be at least 12 characters." if language == "en" else "Ijambo ry'ibanga rigomba kugira inyuguti nibura 12.")
                elif new_password != confirmation:
                    st.error(c["password_mismatch"])
                else:
                    try:
                        _request("POST", "/community/password/reset", payload={"token": reset_token, "new_password": new_password})
                        st.query_params.clear()
                        st.session_state["community_reset_success"] = True
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(_error_message(exc, language))
        return

    if st.session_state.pop("community_reset_success", False):
        st.success(c["password_updated"])

    community_token = st.session_state.get("community_access_token")
    community_expiry = st.session_state.get("community_access_token_expires_at")
    if community_token and (community_expiry is None or time.time() >= community_expiry):
        _clear_community_session(expired=True)
    if st.session_state.pop("community_session_expired", False):
        st.info("Your community session expired. Sign in again to continue." if language == "en" else "Igihe cya konti y'umuryango cyarangiye. Ongera winjire ukomeze.")

    if not st.session_state.get("community_access_token"):
        st.markdown("<style>.st-key-community_auth_panel { max-width: 760px; margin: 1rem auto 2rem; }</style>", unsafe_allow_html=True)
        with st.container(key="community_auth_panel"):
            st.warning(c["privacy"])
            auth_mode = st.radio(
                "Community account", [c["signin"], c["create"]],
                horizontal=True, label_visibility="collapsed", key="community_auth_mode",
            )
            if auth_mode == c["signin"]:
                with st.form("community_sign_in"):
                    email = st.text_input(c["email"], key="community_login_email")
                    password = st.text_input(c["password"], type="password", key="community_login_password")
                    submit = st.form_submit_button(c["signin"], type="primary", use_container_width=True)
                if submit:
                    try:
                        response = _request("POST", "/community/login", payload={"email": email, "password": password})
                        _store_community_session(response)
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(_error_message(exc, language))
                with st.expander(c["forgot_password"]):
                    with st.form("community_password_forgot_form"):
                        reset_email = st.text_input(c["email"], key="community_reset_email")
                        send_reset = st.form_submit_button(c["send_reset"])
                    if send_reset:
                        try:
                            reset_result = _request("POST", "/community/password/forgot", payload={"email": reset_email})
                            st.success(c["reset_requested"])
                            if reset_result.get("development_reset_url"):
                                if reset_result.get("development_email_status") == "accepted":
                                    st.info("The mail server accepted a reset message. If it does not arrive, check spam or use the local reset link below.")
                                elif reset_result.get("development_email_status") == "failed":
                                    st.warning("Email delivery failed in this development environment. Use the local reset link below.")
                                st.link_button(c["reset_dev_link"], reset_result["development_reset_url"], type="primary")
                            elif reset_result.get("development_error"):
                                st.warning(c["reset_dev_error"])
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
            else:
                with st.form("community_register"):
                    display_name = st.text_input(c["name"], max_chars=30)
                    email = st.text_input(c["email"], key="community_register_email")
                    password = st.text_input(c["password"] + (" (at least 12 characters)" if language == "en" else " (inyuguti nibura 12)"), type="password", key="community_register_password")
                    submit = st.form_submit_button(c["create_farmer"], type="primary", use_container_width=True)
                if submit:
                    try:
                        response = _request("POST", "/community/register", payload={
                            "display_name": display_name, "email": email, "password": password,
                        })
                        _store_community_session(response)
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(_error_message(exc, language))
            return

    account = st.session_state.get("community_account", {})
    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.text(f"{c['posting_as']} {account.get('display_name', c['reply_author'])} · {c['farmer']}")
    with top_right:
        if st.button("Sign out", key="community_sign_out"):
            _clear_community_session()
            st.rerun()

    selected_section = st.radio(
        "Community feed", [c["discussion_tab"], c["field_tab"]],
        horizontal=True, label_visibility="collapsed", key="community_feed_section",
    )
    if selected_section == c["field_tab"]:
        _field_reports(st.session_state["community_access_token"], language)
    else:
        with st.container(border=True):
            st.subheader(c["new_post"])
            with st.form("community_new_post", clear_on_submit=True):
                body = st.text_area(c["post_body"], max_chars=5000, height=130, placeholder="What did you notice? What would you like help with?")
                title = st.text_input(c["topic"], max_chars=140, placeholder="Optional — a short title helps others scan the feed")
                submit = st.form_submit_button(c["publish"], type="primary", use_container_width=True)
            if submit:
                if not body.strip():
                    st.warning("Write an update or question before posting.")
                else:
                    post_title = title.strip() or body.strip().splitlines()[0][:137]
                    if len(post_title) < 3:
                        post_title = f"{post_title} — community update"
                    try:
                        _request("POST", "/community/posts", payload={"title": post_title, "body": body.strip()})
                        st.success(c["posted"])
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(_error_message(exc, language))

        try:
            feed_offset = int(st.session_state.get("community_feed_offset", 0))
            posts = _request("GET", f"/community/posts?limit=15&offset={feed_offset}")
        except requests.RequestException as exc:
            st.error(_error_message(exc, language))
            return

        page_post_count = len(posts)
        feed_search = st.text_input(
            "Search these discussions", placeholder="Search titles, updates, or usernames",
            key="community_feed_search",
        ).strip().casefold()
        if feed_search:
            posts = [post for post in posts if feed_search in " ".join((
                str(post.get("title") or ""), str(post.get("body") or ""),
                str((post.get("author") or {}).get("display_name") or ""),
            )).casefold()]
            st.caption("Search covers the posts on this page. Use Older posts to browse further.")

        if not posts:
            st.info("No discussions match this search." if feed_search else c["empty"])

        comments_by_post = {}
        if posts:
            try:
                response = requests.get(
                    f"{API_BASE_URL}/community/comments",
                    params=[("post_ids", str(post["id"])) for post in posts if post.get("id")],
                    headers={"Authorization": f"Bearer {st.session_state['community_access_token']}"},
                    timeout=12,
                )
                response.raise_for_status()
                for comment in response.json():
                    comments_by_post.setdefault(str(comment.get("post_id")), []).append(comment)
            except requests.RequestException as exc:
                st.error(_error_message(exc, language))

        for post in posts:
            post_id = post.get("id")
            author = post.get("author") or {}
            own_post = str(post.get("author_id")) == str(account.get("id"))
            with st.container(border=True):
                st.subheader(post.get("title", "Community update"))
                st.caption(f"{author.get('display_name', c['reply_author'])} · {author.get('role', c['role_farmer'])} · {post.get('created_at', '')}")
                st.write(post.get("body", ""))
                comments = comments_by_post.get(str(post_id), [])
                if comments:
                    st.caption(f"{c['reply_count']} · {min(len(comments), 8)} latest")
                    for comment in reversed(comments[:8]):
                        comment_author = comment.get("author") or {}
                        st.markdown(f"**{comment_author.get('display_name', c['reply_author'])}** · {comment_author.get('role', c['role_farmer'])}")
                        st.write(comment.get("body", ""))
                with st.form(f"community_comment_{post_id}", clear_on_submit=True):
                    reply = st.text_area(c["reply"], max_chars=1500, key=f"reply_{post_id}")
                    reply_submit = st.form_submit_button(c["send_reply"], type="primary")
                if reply_submit:
                    if not reply.strip():
                        st.warning("Write a reply before sending.")
                    else:
                        try:
                            _request("POST", f"/community/posts/{post_id}/comments", payload={"body": reply})
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
                action_cols = st.columns([1, 5])
                if own_post:
                    with action_cols[0].popover(c["delete_post"]):
                        st.warning(c["delete_confirm"])
                        if st.button(c["delete_post"], key=f"delete_own_post_{post_id}", type="primary"):
                            try:
                                _request("DELETE", f"/community/posts/{post_id}")
                                st.success(c["post_deleted"])
                                st.rerun()
                            except requests.RequestException as exc:
                                st.error(_error_message(exc, language))
                else:
                    with action_cols[0].popover("Report content"):
                        with st.form(f"report_post_{post_id}"):
                            reason = st.text_input("Reason (required)", max_chars=500)
                            report = st.form_submit_button("Send to administrators")
                        if report:
                            try:
                                _request("POST", f"/community/posts/{post_id}/report", payload={"reason": reason})
                                st.success("Report sent for administrator review.")
                            except requests.RequestException as exc:
                                st.error(_error_message(exc, language))

        page_cols = st.columns([1, 1, 4])
        with page_cols[0]:
            if feed_offset > 0 and st.button("Newer posts", key="community_feed_newer"):
                st.session_state["community_feed_offset"] = max(0, feed_offset - 15)
                st.rerun()
        with page_cols[1]:
            if page_post_count == 15 and st.button("Older posts", key="community_feed_older"):
                st.session_state["community_feed_offset"] = feed_offset + 15
                st.rerun()
