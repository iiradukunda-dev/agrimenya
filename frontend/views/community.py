"""Farmer discussion feed backed by individually authenticated accounts."""
import requests
import streamlit as st
from datetime import date
from io import BytesIO
from PIL import Image

from utils.config import API_BASE_URL
from utils.i18n import get_current_language

COPY = {
    "en": {
        "title": "Farmer community", "intro": "Share practical experience, ask questions, and learn from other growers.",
        "language": "Language / Ururimi", "warning": "Farmer observations are community reports, not official NISR statistics or verified agronomic advice.",
        "reports": "Field observations", "report_help": "A short field note can help others understand what is happening locally.",
        "district": "District", "crop": "Crop", "date": "Date observed", "symptoms": "What did you notice? (optional)",
        "notes": "Extra details (optional)", "photo": "Photo (optional, compressed before upload)", "save_report": "Share field observation",
        "saved": "Observation shared.", "no_reports": "No field observations yet.", "unknown_author": "Community member",
        "signin": "Sign in", "create": "Create account", "email": "Email address", "password": "Password",
        "name": "Username (3-30 letters, numbers, or underscores)", "create_farmer": "Create farmer account", "signout": "Sign out",
        "new_post": "Share an update or question", "topic": "Topic", "post_body": "Your experience or question",
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
    },
    "rw": {
        "title": "Umuryango w'abahinzi", "intro": "Sangiza abandi ubunararibonye, ubaze ibibazo kandi wungurane ubumenyi.",
        "language": "Language / Ururimi", "warning": "Ibyo abahinzi batangaje ni amakuru y'umuryango gusa; si imibare yemewe ya NISR cyangwa inama zemejwe.",
        "reports": "Amakuru yo mu murima", "report_help": "Andika muri make ibyo wabonye kugira ngo bifashe abandi kumenya uko umurima umeze.",
        "district": "Akarere", "crop": "Igihingwa", "date": "Itariki waboneyeho", "symptoms": "Wabonye iki? (si ngombwa)",
        "notes": "Ibindi bisobanuro (si ngombwa)", "photo": "Ifoto (si ngombwa; iragabanywa mbere yo koherezwa)", "save_report": "Sangiza amakuru yo mu murima",
        "saved": "Amakuru yo mu murima yasangijwe.", "no_reports": "Nta makuru yo mu murima arahari.", "unknown_author": "Umunyamuryango",
        "signin": "Injira", "create": "Fungura konti", "email": "Imeyili", "password": "Ijambo ry'ibanga",
        "name": "Izina ukoresha (inyuguti, imibare cyangwa _; 3-30)", "create_farmer": "Fungura konti y'umuhinzi", "signout": "Sohoka",
        "new_post": "Sangiza amakuru cyangwa ikibazo", "topic": "Umutwe", "post_body": "Ibyo wahuye na byo cyangwa ikibazo",
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
    },
    "fr": {
        "title": "Communauté des agriculteurs", "intro": "Partagez votre expérience pratique, posez des questions et apprenez d'autres producteurs.",
        "language": "Langue / Ururimi", "warning": "Les observations des agriculteurs sont des rapports communautaires, et non des statistiques officielles du NISR ou des avis agronomiques vérifiés.",
        "reports": "Observations de terrain", "report_help": "Une brève note de terrain peut aider les autres à comprendre ce qui se passe localement.",
        "district": "District", "crop": "Culture", "date": "Date d'observation", "symptoms": "Qu'avez-vous remarqué ? (optionnel)",
        "notes": "Détails supplémentaires (optionnel)", "photo": "Photo (optionnel, compressée avant l'envoi)", "save_report": "Partager l'observation de terrain",
        "saved": "Observation partagée.", "no_reports": "Aucune observation de terrain pour le moment.", "unknown_author": "Membre de la communauté",
        "signin": "Connexion", "create": "Créer un compte", "email": "Adresse e-mail", "password": "Mot de passe",
        "name": "Nom d'utilisateur (3-30 lettres, chiffres ou _)", "create_farmer": "Créer un compte agriculteur", "signout": "Déconnexion",
        "new_post": "Partager une actualité ou une question", "topic": "Sujet", "post_body": "Votre expérience ou question",
        "publish": "Publier dans la communauté", "posted": "Votre publication a été partagée.", "replies": "Lire les réponses et participer à la discussion",
        "reply": "Ajouter une réponse", "send_reply": "Répondre", "report": "Signaler le contenu", "reason": "Motif (obligatoire)",
        "send_report": "Envoyer aux administrateurs", "report_sent": "Signalement envoyé pour examen administratif.",
        "privacy": "Les comptes pilotes ne sont pas vérifiés par e-mail. Évitez de partager des informations financières, familiales ou de contact privées.",
        "account_name": "Publié par", "farmer": "Compte agriculteur", "empty": "Aucune discussion pour l'instant. Lancez la première en partageant une observation ou une question.",
        "unavailable": "Choix de districts indisponibles. Vérifiez votre connexion et réessayez.", "crop_required": "Entrez le nom de la culture.",
        "valid_photo": "Choisissez une photo valide.", "photo_too_large": "La photo est trop volumineuse. Choisissez une image plus petite.",
        "farmer_observation": "Observation d'agriculteur", "photo_caption": "Photo soumise par un agriculteur",
        "posting_as": "Publié en tant que", "reply_author": "Membre de la communauté", "role_farmer": "agriculteur",
        "delete_post": "Supprimer ma publication", "delete_confirm": "Supprimer cette publication ? Cette action est irréversible.",
        "post_deleted": "Votre publication a été supprimée.",
        "discussion_tab": "Discussions", "field_tab": "Observations de terrain", "reply_count": "Réponses",
        "delete_observation": "Supprimer mon observation", "observation_deleted": "Observation de terrain supprimée.",
        "observation_delete_confirm": "Supprimer cette observation de terrain et sa photo ? Cette action est irréversible.",
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
    if zones:
        district_names = sorted({str(item.get("district", "")) for item in zones if item.get("district")})
        zones_by_district = {str(item.get("district")): item for item in zones if item.get("district")}
        with st.expander(c["report_help"], expanded=False):
            with st.form("community_field_observation", clear_on_submit=True):
                district = st.selectbox(c["district"], district_names)
                crop = st.text_input(c["crop"], max_chars=50, placeholder="e.g. Maize / Ibigori")
                observed_on = st.date_input(c["date"], value=date.today())
                symptoms = st.text_area(c["symptoms"], max_chars=500, height=90)
                notes = st.text_area(c["notes"], max_chars=1000, height=90)
                photo = st.file_uploader(c["photo"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=False)
                submit = st.form_submit_button(c["save_report"], type="primary", use_container_width=True)
            if submit:
                zone = zones_by_district.get(str(district))
                if not zone or not zone.get("id"):
                    st.error(c.get("unavailable", "Zone information is unavailable."))
                elif not crop.strip():
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
                    return ("Use a username of 3-30 letters, numbers, or underscores." if language == "en"
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
    if language not in COPY:
        language = "en"
    c = COPY[language]

    if not st.session_state.get("community_access_token"):
        from components.cards import login_card_header, security_trust_footer
        col_l, col_center, col_r = st.columns([1, 1.8, 1])
        with col_center:
            with st.container(border=True):
                sprout_icon = """<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M7 20h10"/>
                    <path d="M10 20c0-4 1-6 2-10"/>
                    <path d="M12 10a4 4 0 0 1 7-3 4 4 0 0 1-3 7 4 4 0 0 1-4-4z"/>
                    <path d="M12 14a4 4 0 0 0-7-3 4 4 0 0 0 3 7 4 4 0 0 0 4-4z"/>
                </svg>"""
                badge_title = "GROWER NETWORK" if language == "en" else "UMURYANGO W'ABAHINZI" if language == "rw" else "RÉSEAU AGRICOLE"
                login_card_header(
                    title=c["title"],
                    subtitle=c["intro"],
                    badge_text=badge_title,
                    icon=sprout_icon,
                    accent_color="#10b981",
                )
                sign_in, create_account = st.tabs([c["signin"], c["create"]])
                with sign_in:
                    with st.form("community_sign_in"):
                        email = st.text_input(c["email"], placeholder="farmer@cooperative.rw", key="community_login_email")
                        password = st.text_input(c["password"], type="password", placeholder="••••••••••••", key="community_login_password")
                        submit = st.form_submit_button(f"{c['signin']} →", type="primary", use_container_width=True)
                    if submit:
                        try:
                            response = _request("POST", "/community/login", payload={"email": email, "password": password})
                            st.session_state["community_access_token"] = response["access_token"]
                            st.session_state["community_account"] = response.get("account", {})
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
                with create_account:
                    with st.form("community_register"):
                        display_name = st.text_input(c["name"], placeholder="e.g. Jean_Gasabo", max_chars=80)
                        email = st.text_input(c["email"], placeholder="farmer@cooperative.rw", key="community_register_email")
                        password = st.text_input(
                            c["password"] + (" (at least 12 characters)" if language == "en" else " (inyuguti nibura 12)"),
                            type="password",
                            placeholder="Min. 12 characters",
                            key="community_register_password",
                        )
                        submit = st.form_submit_button(f"{c['create_farmer']} →", type="primary", use_container_width=True)
                    if submit:
                        try:
                            response = _request("POST", "/community/register", payload={
                                "display_name": display_name, "email": email, "password": password,
                            })
                            st.session_state["community_access_token"] = response["access_token"]
                            st.session_state["community_account"] = response.get("account", {})
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
                security_trust_footer(
                    message="Privacy Protected" if language == "en" else "Umutekano urarinzwe" if language == "rw" else "Confidentialité Protégée",
                    session_info="Verified Grower Network" if language == "en" else "Koperative z'Abahinzi" if language == "rw" else "Réseau Coopératif",
                )
        return

    st.title(c["title"])
    st.write(c["intro"])
    st.caption(c["warning"])

    account = st.session_state.get("community_account", {})
    from components.cards import authenticated_session_badge
    display_name = account.get('display_name') or c['reply_author']
    email = account.get('email', '')
    if authenticated_session_badge(display_name=display_name, email=email, role=c['farmer'], key_prefix="community"):
        st.session_state.pop("community_access_token", None)
        st.session_state.pop("community_account", None)
        st.rerun()

    discussions_tab, observations_tab = st.tabs([c["discussion_tab"], c["field_tab"]])
    with observations_tab:
        _field_reports(st.session_state["community_access_token"], language)

    with discussions_tab:
        with st.container(border=True):
            st.subheader(c["new_post"])
            with st.form("community_new_post", clear_on_submit=True):
                title = st.text_input(c["topic"], max_chars=140)
                body = st.text_area(c["post_body"], max_chars=5000, height=120)
                submit = st.form_submit_button(c["publish"], type="primary", use_container_width=True)
            if submit:
                try:
                    _request("POST", "/community/posts", payload={"title": title, "body": body})
                    st.success(c["posted"])
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(_error_message(exc, language))

        try:
            posts = _request("GET", "/community/posts?limit=30")
        except requests.RequestException as exc:
            st.error(_error_message(exc, language))
            return

        if not posts:
            st.info(c["empty"])

        for post in posts:
            post_id = post.get("id")
            author = post.get("author") or {}
            own_post = str(post.get("author_id")) == str(account.get("id"))
            with st.container(border=True):
                st.subheader(post.get("title", "Community update"))
                st.caption(f"{author.get('display_name', c['reply_author'])} · {author.get('role', c['role_farmer'])} · {post.get('created_at', '')}")
                st.write(post.get("body", ""))
                try:
                    comments = _request("GET", f"/community/posts/{post_id}/comments")
                    st.caption(f"{c['reply_count']} · {len(comments)}")
                    for comment in comments:
                        comment_author = comment.get("author") or {}
                        st.markdown(f"**{comment_author.get('display_name', c['reply_author'])}** · {comment_author.get('role', c['role_farmer'])}")
                        st.write(comment.get("body", ""))
                except requests.RequestException as exc:
                    comments = []
                    st.error(_error_message(exc, language))
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
