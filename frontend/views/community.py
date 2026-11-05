import time
from datetime import date
from io import BytesIO
from PIL import Image

import requests
import streamlit as st
from components.errors import error_boundary
from utils.config import API_BASE_URL
from utils.api_client import AUTH_SESSION_SECONDS, request_api
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
        "email_accepted": "The mail server accepted the message, but delivery is not guaranteed. Check your inbox and spam folder, or use the local link below.",
        "email_failed": "Email delivery failed in this development setup. Use the local one-time link below.",
        "email_not_configured": "Email delivery is not configured in this development setup. Use the local one-time link below.",
        "google_signin": "Continue with Google",
        "email_separator": "or sign in with email",
        "google_new_account_note": "Google sign-in can create a farmer account if you are new. Your Google email must be verified.",
        "google_error_cancelled": "Google sign-in was cancelled.",
        "google_error_invalid_state": "This Google sign-in request could not be verified. Start again.",
        "google_error_expired": "This Google sign-in request expired. Start again.",
        "google_error_invalid_identity": "Google could not verify this sign-in. Start again.",
        "google_error_unverified_email": "Google must confirm your email address before it can be used here.",
        "google_error_account_unavailable": "This Community account is unavailable. Contact an administrator if you think this is an error.",
        "google_error_account_conflict": "This email is already linked to another Google account.",
        "google_error_account_link_required": "This email already has a Community account. Sign in with its existing method; Google can link automatically only when Google controls that email domain.",
        "google_error_unavailable": "Google sign-in could not be completed. Please try again.",
        "google_error_generic": "Google sign-in could not be completed. Please try again.",
        "password_updated": "Password updated. Sign in with your new password.", "password_mismatch": "The passwords do not match.",
        "privacy": "Use a verified email to protect your account. Avoid sharing private contact, financial, or household information.",
        "verify_title": "Verify your email", "verify_help": "Open the one-time link sent to your email, then verify it here.",
        "verify_button": "Verify email", "verify_success": "Email verified. You can now sign in.",
        "verify_resend": "Resend verification email", "verify_resend_help": "Enter your email if you need a new verification link.",
        "verify_sent": "If your account needs verification, a new link will be sent.", "verify_dev_link": "Open the local verification link",
        "verify_dev_error": "Could not prepare the verification link. Check the backend and database connection.",
        "register_sent": "Account created. Check your email to verify it before signing in.",
        "welcome_back": "Welcome back", "signin_subtitle": "Sign in to your account to continue.",
        "password_minimum": "At least 12 characters", "field_form_help": "Add a location, crop, date, and a brief note. Photos are optional; observations are not verified diagnoses.",
        "crop_example": "e.g. Maize", "symptoms_hint": "Describe what you saw, where it appears, and when it started.",
        "district_filter": "Filter by district", "crop_filter": "Filter by crop", "filter_value_hint": "Type an exact value; leave blank to show all.",
        "all_districts": "All districts",
        "newer_posts": "Newer posts", "older_posts": "Older posts",
        "older_observations": "Older observations", "newer_observations": "Newer observations",
        "profile_title": "Community profile", "profile_username": "Username", "profile_help": "Your username appears beside your posts and observations.",
        "save_profile": "Save profile", "profile_saved": "Username updated.", "profile_conflict": "That username is already in use.",
        "notification_title": "Replies to your discussions", "notification_empty": "No new replies.",
        "notification_item": "{actor} replied to “{title}”.", "mark_notifications_read": "Mark all as read",
        "notification_read": "Notifications marked as read.", "report_observation": "Report observation",
        "report_observation_help": "Tell administrators why this observation should be reviewed.",
        "report_required": "Enter a reason of at least 3 characters.",
        "post_body_hint": "What did you notice? What would you like help with?",
        "topic_hint": "Optional — a short title helps others scan the feed",
        "discussion_search": "Search these discussions", "discussion_search_hint": "Search titles, updates, or usernames",
        "discussion_search_scope": "Search covers the posts on this page. Use Older posts to browse further.",
        "discussion_no_match": "No discussions match this search.", "write_before_posting": "Write an update or question before posting.",
        "write_before_reply": "Write a reply before sending.", "report_content": "Report content",
        "report_reason": "Reason (required)", "send_to_admins": "Send to administrators",
        "report_sent_confirmation": "Report sent for administrator review.",
        "community_retry": "Retry", "server_starting": "The server is still starting up. Please try again in a moment.",
        "server_unreachable": "Cannot reach the server. Check the backend connection and try again.",
        "server_error": "The server returned an error. Please try again.",
        "request_error": "The server could not complete that request. Please try again.",
        "session_expired": "Your community session expired. Sign in again to continue.",
        "password_min_error": "Password must be at least 12 characters.",
        "username_invalid": "Use a username of 3–30 letters, numbers, or underscores.",
        "email_invalid": "Enter a valid email address.", "verify_link_subtitle": "Open the one-time link sent to your email, then verify it here.",
        "reset_link_subtitle": "Use at least 12 characters. The reset link can be used once and expires after 30 minutes.",
        "admin_portal_link": "Administrator or agronomist? Go to Administrator Portal",
        "report_target_missing": "This field observation could not be found.",
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
        "email_accepted": "Seriveri ya imeyili yemeye ubutumwa, ariko ntibyemeza ko bwageze. Reba muri inbox na spam, cyangwa ukoreshe umurongo uri hepfo.",
        "email_failed": "Kohereza imeyili ntibyashobotse muri iyi porogaramu yo kugerageza. Koresha umurongo uri hepfo.",
        "email_not_configured": "Kohereza imeyili ntibirashyirwaho muri iyi porogaramu yo kugerageza. Koresha umurongo uri hepfo.",
        "google_signin": "Komeza ukoresheje Google",
        "email_separator": "cyangwa winjire ukoresheje imeyili",
        "google_new_account_note": "Google ishobora kugufungurira konti y'umuhinzi niba utarayifungura. Imeyili ya Google igomba kuba yemejwe.",
        "google_error_cancelled": "Wahagaritse kwinjira ukoresheje Google.",
        "google_error_invalid_state": "Ntitwashoboye kugenzura ubu busabe bwa Google. Ongera utangire.",
        "google_error_expired": "Ubu busabe bwa Google bwarengeje igihe. Ongera utangire.",
        "google_error_invalid_identity": "Google ntiyashoboye kugenzura ubu buryo bwo kwinjira. Ongera ugerageze.",
        "google_error_unverified_email": "Google igomba kubanza kwemeza imeyili yawe.",
        "google_error_account_unavailable": "Iyi konti y'umuryango ntiboneka. Baza umuyobozi niba utekereza ko ari ikosa.",
        "google_error_account_conflict": "Iyi imeyili isanzwe ihujwe na indi konti ya Google.",
        "google_error_account_link_required": "Iyi imeyili isanzwe ifite konti y'umuryango. Injira ukoresheje uburyo wari usanzwe ukoresha; Google ihuza mu buryo bwikora gusa iyo igenzura iyo domeni ya imeyili.",
        "google_error_unavailable": "Ntibyashobotse kwinjira ukoresheje Google. Ongera ugerageze.",
        "google_error_generic": "Ntibyashobotse kwinjira ukoresheje Google. Ongera ugerageze.",
        "password_updated": "Ijambo ry'ibanga ryahinduwe. Injira ukoresheje irishya.", "password_mismatch": "Amagambo y'ibanga ntahura.",
        "privacy": "Koresha imeyili yemejwe kugira ngo urinde konti yawe. Irinde gusangiza abandi telefoni, amakuru y'amafaranga cyangwa ay'urugo.",
        "verify_title": "Emeza imeyili yawe", "verify_help": "Fungura umurongo wihariye woherejwe kuri imeyili yawe, hanyuma ubyemeze hano.",
        "verify_button": "Emeza imeyili", "verify_success": "Imeyili yemejwe. Ushobora kwinjira.",
        "verify_resend": "Ongera wohereze imeyili yo kwemeza", "verify_resend_help": "Andika imeyili niba ukeneye umurongo mushya.",
        "verify_sent": "Niba konti yawe itaremezwa, umurongo mushya uraza koherezwa.", "verify_dev_link": "Fungura umurongo wo kwemeza kuri mudasobwa yawe",
        "verify_dev_error": "Ntibyashobotse gutegura umurongo wo kwemeza. Reba backend na database.",
        "register_sent": "Konti yafunguwe. Reba imeyili yawe uyemeze mbere yo kwinjira.",
        "welcome_back": "Ongera uze neza", "signin_subtitle": "Injira muri konti yawe ukomeze.",
        "password_minimum": "Inyuguti nibura 12", "field_form_help": "Ongeraho aho umurima uherereye, igihingwa, itariki n'ibisobanuro bigufi. Ifoto si ngombwa; aya makuru si isuzuma ryemejwe.",
        "crop_example": "Urugero: Ibigori", "symptoms_hint": "Sobanura ibyo wabonye, aho biri n'igihe byatangiriye.",
        "district_filter": "Shakisha hakurikijwe akarere", "crop_filter": "Shakisha hakurikijwe igihingwa", "filter_value_hint": "Andika agaciro nyako; siga ubusa kugira ngo werekane byose.",
        "all_districts": "Uturere twose",
        "newer_posts": "Inyandiko nshya", "older_posts": "Inyandiko zishaje",
        "older_observations": "Amakuru ashaje", "newer_observations": "Amakuru mashya",
        "profile_title": "Konti y'umuryango", "profile_username": "Izina ukoresha", "profile_help": "Izina ryawe rigaragara ku nyandiko n'amakuru utanga.",
        "save_profile": "Bika konti", "profile_saved": "Izina ukoresha ryahinduwe.", "profile_conflict": "Iri zina risanzwe rikoreshwa.",
        "notification_title": "Ibisubizo ku biganiro byawe", "notification_empty": "Nta bisubizo bishya.",
        "notification_item": "{actor} yasubije “{title}”.", "mark_notifications_read": "Shyira byose mu byasomwe",
        "notification_read": "Amakuru mashya yashyizwe mu byasomwe.", "report_observation": "Tanga ikirego ku makuru",
        "report_observation_help": "Sobanurira abayobozi impamvu aya makuru akwiye gusuzumwa.",
        "report_required": "Andika impamvu ifite inyuguti nibura 3.",
        "post_body_hint": "Wabonye iki? Ni iki wifuza ko abandi bagufashamo?",
        "topic_hint": "Si ngombwa — umutwe mugufi worohereza abandi gusoma",
        "discussion_search": "Shakisha mu biganiro", "discussion_search_hint": "Shakisha imitwe, amakuru cyangwa amazina",
        "discussion_search_scope": "Gushakisha bikorerwa ku nyandiko ziri kuri uru rupapuro. Kanda ku zishaje kugira ngo urebe izindi.",
        "discussion_no_match": "Nta biganiro bihuye n'ibyo washakishije.", "write_before_posting": "Andika amakuru cyangwa ikibazo mbere yo gusangiza abandi.",
        "write_before_reply": "Andika igisubizo mbere yo kohereza.", "report_content": "Tanga ikirego ku makuru",
        "report_reason": "Impamvu (ni ngombwa)", "send_to_admins": "Ohereza ku bayobozi",
        "report_sent_confirmation": "Ikirego cyoherejwe ku bayobozi kugira ngo bagisuzume.",
        "community_retry": "Ongera ugerageze", "server_starting": "Seriveri iracyatangira. Ongera ugerageze mu kanya.",
        "server_unreachable": "Ntibishobotse kugera kuri seriveri. Reba backend wongere ugerageze.",
        "server_error": "Seriveri yagaragaje ikosa. Ongera ugerageze.",
        "request_error": "Seriveri ntiyashoboye kurangiza ubu busabe. Ongera ugerageze.",
        "session_expired": "Igihe cya konti y'umuryango cyarangiye. Ongera winjire ukomeze.",
        "password_min_error": "Ijambo ry'ibanga rigomba kugira inyuguti nibura 12.",
        "username_invalid": "Koresha inyuguti 3–30 zigizwe n'inyuguti, imibare cyangwa _.",
        "email_invalid": "Andika imeyili yemewe.", "verify_link_subtitle": "Fungura umurongo woherejwe kuri imeyili yawe, hanyuma ubyemeze hano.",
        "reset_link_subtitle": "Koresha inyuguti nibura 12. Umurongo ukoreshwa rimwe kandi urangira nyuma y'iminota 30.",
        "admin_portal_link": "Uri umuyobozi cyangwa umuhanga mu buhinzi? Fungura urubuga rw'abayobozi",
        "report_target_missing": "Aya makuru yo mu murima ntabonetse.",
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
        "wa_title": "Utiliser Agri-Menya sur WhatsApp",
        "wa_intro": "Ouvrez une conversation pour accéder aux données agricoles par district et aux outils d'alerte sans vous connecter au site.",
        "wa_commands": "Envoyez HELP pour afficher le menu. Essayez DISTRICT <nom>, RANK <culture>, SUBSCRIBE <district> [culture], STATUS, ALERTS ou LANG RW. Envoyez START uniquement pour recevoir des alertes WhatsApp ; STOP permet de se désinscrire.",
        "wa_pending": "Le service WhatsApp n'est pas encore activé pour les utilisateurs. Les services du site restent disponibles.",
        "wa_unavailable": "La disponibilité de WhatsApp n'a pas pu être vérifiée. Vous pouvez continuer sur le site.",
        "wa_open": "Ouvrir la conversation WhatsApp Agri-Menya",
        "confirm_password": "Confirmer le nouveau mot de passe", "email_accepted": "Le serveur de messagerie a accepté le message, sans garantir sa livraison. Vérifiez votre boîte de réception et les courriers indésirables, ou utilisez le lien local ci-dessous.",
        "email_failed": "L'envoi du courriel a échoué dans cet environnement de développement. Utilisez le lien local à usage unique ci-dessous.",
        "email_not_configured": "L'envoi de courriels n'est pas configuré dans cet environnement de développement. Utilisez le lien local à usage unique ci-dessous.",
        "email_separator": "ou connectez-vous par e-mail", "forgot_password": "Mot de passe oublié ?",
        "google_error_account_conflict": "Cette adresse e-mail est déjà associée à un autre compte Google.",
        "google_error_account_link_required": "Cette adresse e-mail a déjà un compte communautaire. Connectez-vous avec la méthode existante ; Google ne peut associer automatiquement le compte que si Google contrôle le domaine de cette adresse.",
        "google_error_account_unavailable": "Ce compte communautaire est indisponible. Contactez un administrateur si vous pensez qu'il s'agit d'une erreur.",
        "google_error_cancelled": "La connexion Google a été annulée.",
        "google_error_expired": "Cette demande de connexion Google a expiré. Recommencez.",
        "google_error_generic": "La connexion Google n'a pas abouti. Veuillez réessayer.",
        "google_error_invalid_identity": "Google n'a pas pu vérifier cette connexion. Recommencez.",
        "google_error_invalid_state": "Cette demande de connexion Google n'a pas pu être vérifiée. Recommencez.",
        "google_error_unavailable": "La connexion Google n'a pas abouti. Veuillez réessayer.",
        "google_error_unverified_email": "Google doit vérifier votre adresse e-mail avant son utilisation ici.",
        "google_new_account_note": "La connexion Google peut créer un compte agriculteur. Votre adresse Google doit être vérifiée.",
        "google_signin": "Continuer avec Google", "password_mismatch": "Les mots de passe ne correspondent pas.",
        "password_updated": "Mot de passe mis à jour. Connectez-vous avec le nouveau mot de passe.",
        "register_sent": "Compte créé. Vérifiez votre adresse e-mail avant de vous connecter.",
        "reset_dev_error": "Impossible de créer le lien de réinitialisation. Vérifiez l'accès du serveur à la base de données.",
        "reset_dev_link": "Ouvrir le lien de réinitialisation à usage unique",
        "reset_password": "Choisir un nouveau mot de passe", "reset_requested": "Si un compte correspond à cette adresse, un lien de réinitialisation sera envoyé.",
        "save_password": "Mettre à jour le mot de passe", "send_reset": "Envoyer le lien de réinitialisation",
        "verify_button": "Vérifier l'e-mail", "verify_dev_error": "Impossible de préparer le lien de vérification. Vérifiez le serveur et la base de données.",
        "verify_dev_link": "Ouvrir le lien local de vérification", "verify_help": "Ouvrez le lien à usage unique envoyé à votre adresse, puis vérifiez-la ici.",
        "verify_resend": "Renvoyer le courriel de vérification", "verify_resend_help": "Saisissez votre adresse e-mail pour recevoir un nouveau lien de vérification.",
        "verify_sent": "Si votre compte doit être vérifié, un nouveau lien sera envoyé.",
        "verify_success": "Adresse e-mail vérifiée. Vous pouvez maintenant vous connecter.",
        "verify_title": "Vérifier votre adresse e-mail",
        "welcome_back": "Bon retour", "signin_subtitle": "Connectez-vous pour continuer.",
        "password_minimum": "12 caractères minimum",
        "field_form_help": "Ajoutez un lieu, une culture, une date et une brève note. La photo est facultative ; ces observations ne sont pas des diagnostics vérifiés.",
        "crop_example": "Ex. : Maïs", "symptoms_hint": "Décrivez ce que vous avez observé, où cela apparaît et depuis quand.",
        "district_filter": "Filtrer par district", "crop_filter": "Filtrer par culture", "filter_value_hint": "Saisissez une valeur exacte ; laissez vide pour tout afficher.",
        "all_districts": "Tous les districts",
        "newer_posts": "Publications plus récentes", "older_posts": "Publications précédentes",
        "older_observations": "Observations précédentes", "newer_observations": "Observations plus récentes",
        "profile_title": "Profil communautaire", "profile_username": "Nom d'utilisateur",
        "profile_help": "Votre nom d'utilisateur apparaît avec vos publications et observations.",
        "save_profile": "Enregistrer le profil", "profile_saved": "Nom d'utilisateur mis à jour.",
        "profile_conflict": "Ce nom d'utilisateur est déjà utilisé.",
        "notification_title": "Réponses à vos discussions", "notification_empty": "Aucune nouvelle réponse.",
        "notification_item": "{actor} a répondu à « {title} ».", "mark_notifications_read": "Tout marquer comme lu",
        "notification_read": "Notifications marquées comme lues.", "report_observation": "Signaler l'observation",
        "report_observation_help": "Expliquez aux administrateurs pourquoi cette observation doit être examinée.",
        "report_required": "Saisissez un motif d'au moins 3 caractères.",
        "post_body_hint": "Qu'avez-vous observé ? De quelle aide avez-vous besoin ?",
        "topic_hint": "Facultatif — un titre court facilite la lecture du fil",
        "discussion_search": "Rechercher dans les discussions", "discussion_search_hint": "Rechercher des titres, publications ou noms d'utilisateur",
        "discussion_search_scope": "La recherche porte sur les publications de cette page. Utilisez Publications précédentes pour continuer.",
        "discussion_no_match": "Aucune discussion ne correspond à cette recherche.",
        "write_before_posting": "Rédigez une actualité ou une question avant de publier.",
        "write_before_reply": "Rédigez une réponse avant de l'envoyer.",
        "report_content": "Signaler le contenu", "report_reason": "Motif (obligatoire)",
        "send_to_admins": "Envoyer aux administrateurs",
        "report_sent_confirmation": "Signalement envoyé pour examen administratif.",
        "community_retry": "Réessayer",
        "server_starting": "Le serveur démarre encore. Veuillez réessayer dans un instant.",
        "server_unreachable": "Impossible de joindre le serveur. Vérifiez la connexion au backend et réessayez.",
        "server_error": "Le serveur a rencontré une erreur. Veuillez réessayer.",
        "request_error": "Le serveur n'a pas pu traiter cette demande. Veuillez réessayer.",
        "session_expired": "Votre session communautaire a expiré. Reconnectez-vous pour continuer.",
        "password_min_error": "Le mot de passe doit comporter au moins 12 caractères.",
        "username_invalid": "Utilisez un nom de 3 à 30 lettres, chiffres ou traits de soulignement.",
        "email_invalid": "Saisissez une adresse e-mail valide.",
        "verify_link_subtitle": "Ouvrez le lien à usage unique envoyé à votre adresse, puis vérifiez-la ici.",
        "reset_link_subtitle": "Utilisez au moins 12 caractères. Le lien est à usage unique et expire après 30 minutes.",
        "admin_portal_link": "Administrateur ou agronome ? Accéder au portail administrateur",
        "report_target_missing": "Cette observation de terrain est introuvable.",
    },
}


@st.cache_data(ttl=600, show_spinner=False)
def _district_zones() -> list[dict]:
    response = request_api("GET", "/segmentation/zones", timeout=8)
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
        with st.popover(c["report_help"], use_container_width=True):
            st.caption(c["field_form_help"])
            with st.form("community_field_observation", clear_on_submit=True):
                selected_zone_label = st.selectbox(c["district"], list(zone_by_label))
                crop = st.text_input(c["crop"], max_chars=50, placeholder=c["crop_example"])
                observed_on = st.date_input(c["date"], value=date.today())
                symptoms = st.text_area(c["symptoms"], max_chars=500, height=110, placeholder=c["symptoms_hint"])
                notes = st.text_area(c["notes"], max_chars=1000, height=90)
                photo = st.file_uploader(c["photo"], type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=False)
                submit = st.form_submit_button(c["save_report"], type="primary", use_container_width=True)
            if submit:
                zone = zone_by_label.get(str(selected_zone_label))
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
                            response = request_api(
                                "POST",
                                f"{API_BASE_URL}/community/field-reports",
                                data={"zone_id": zone["id"], "crop": crop.strip(), "observed_on": observed_on.isoformat(),
                                      "symptoms": symptoms.strip(), "notes": notes.strip()},
                                files=files, headers={"Authorization": f"Bearer {token}"}, timeout=25,
                            )
                            response.raise_for_status()
                            st.success(c["saved"])
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
    district_options = sorted({
        str(item.get("district")).strip()
        for item in zones
        if item.get("district") and str(item.get("district")).strip()
    })
    selected_district = st.selectbox(
        c["district_filter"], ["", *district_options],
        format_func=lambda value: value or c["all_districts"],
        key="community_field_district_filter",
    )
    crop_filter = st.text_input(
        c["crop_filter"], placeholder=c["filter_value_hint"],
        key="community_field_crop_filter",
    ).strip()
    filter_values = (
        selected_district,
        crop_filter,
    )
    if st.session_state.get("community_field_report_filters") != filter_values:
        st.session_state["community_field_report_filters"] = filter_values
        st.session_state["community_field_report_offset"] = 0
    report_offset = int(st.session_state.get("community_field_report_offset", 0))
    report_params = {"limit": 10, "offset": report_offset}
    if filter_values[0]:
        report_params["district"] = filter_values[0]
    if filter_values[1]:
        report_params["crop"] = filter_values[1]
    try:
        response = request_api(
            "GET", f"{API_BASE_URL}/community/field-reports", params=report_params,
            headers={"Authorization": f"Bearer {token}"}, timeout=10,
        )
        response.raise_for_status()
        reports = response.json()
    except requests.RequestException as exc:
        st.error(_error_message(exc, language))
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
                            response = request_api(
                                "DELETE",
                                f"{API_BASE_URL}/community/field-reports/{report['id']}",
                                headers={"Authorization": f"Bearer {token}"}, timeout=20,
                            )
                            response.raise_for_status()
                            st.success(c["observation_deleted"])
                            st.rerun()
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))
            else:
                with st.popover(c["report_observation"]):
                    st.caption(c["report_observation_help"])
                    with st.form(f"report_field_observation_{report.get('id')}"):
                        reason = st.text_input(c["report_reason"], max_chars=500)
                        report_submit = st.form_submit_button(c["send_to_admins"])
                    if report_submit:
                        if len(reason.strip()) < 3:
                            st.warning(c["report_required"])
                        else:
                            try:
                                _request(
                                    "POST",
                                    f"/community/field-reports/{report['id']}/report",
                                    payload={"reason": reason.strip()},
                                )
                                st.success(c["report_sent_confirmation"])
                            except requests.RequestException as exc:
                                st.error(_error_message(exc, language))

    report_page_cols = st.columns(2)
    with report_page_cols[0]:
        if report_offset > 0 and st.button(c["newer_observations"], key="community_field_reports_newer"):
            st.session_state["community_field_report_offset"] = max(0, report_offset - 10)
            st.rerun()
    with report_page_cols[1]:
        if len(reports) == 10 and st.button(c["older_observations"], key="community_field_reports_older"):
            st.session_state["community_field_report_offset"] = report_offset + 10
            st.rerun()


def _request(method: str, path: str, *, payload: dict | None = None):
    token = st.session_state.get("community_access_token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if method.upper() == "POST" and path in {
        "/community/login",
        "/community/register",
        "/community/password/forgot",
        "/community/password/reset",
        "/community/email/verify",
        "/community/email/verification/resend",
    }:
        from utils.api_client import ensure_api_awake

        ensure_api_awake()
    response = request_api(
        method, f"{API_BASE_URL}{path}", json=payload, headers=headers, timeout=20
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _community_comments_for_posts(posts: list[dict], token: str) -> list[dict]:
    post_ids = [str(post["id"]) for post in posts if post.get("id")]
    if not post_ids:
        return []
    response = request_api(
        "GET",
        "/community/comments",
        params=[("post_ids", post_id) for post_id in post_ids],
        headers={"Authorization": f"Bearer {token}"},
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60, show_spinner=False)
def _google_sign_in_status() -> bool:
    response = request_api("GET", "/community/auth/google/status", timeout=5)
    response.raise_for_status()
    return bool(response.json().get("enabled"))


def _google_sign_in_enabled() -> bool:
    try:
        return _google_sign_in_status()
    except requests.RequestException:
        return False


def _show_development_mail_status(result: dict, language: str) -> None:
    """Explain local mail delivery honestly and leave production responses generic."""
    c = COPY[language]
    status_value = result.get("development_email_status")
    if status_value == "accepted":
        st.info(c["email_accepted"])
    elif status_value == "failed":
        st.warning(c["email_failed"])
    elif status_value == "not_configured":
        st.warning(c["email_not_configured"])


def _store_community_session(response: dict) -> None:
    st.session_state["community_access_token"] = response["access_token"]
    st.session_state["community_access_token_expires_at"] = time.time() + int(
        response.get("expires_in", AUTH_SESSION_SECONDS)
    )
    st.session_state["community_account"] = response.get("account", {})


def _clear_community_session(*, expired: bool = False) -> None:
    st.session_state.pop("community_access_token", None)
    st.session_state.pop("community_access_token_expires_at", None)
    st.session_state.pop("community_account", None)
    if expired:
        st.session_state["community_session_expired"] = True


def _error_message(exc: requests.RequestException, language: str = "en") -> str:
    c = COPY.get(language, COPY["en"])
    if exc.response is None:
        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return c["server_starting"]
        return c["server_unreachable"]
    if exc.response.status_code >= 500:
        return c["server_error"]
    if exc.response is not None:
        try:
            detail = exc.response.json().get("detail")
            if isinstance(detail, str):
                translations = {
                    "That username is already in use": c["profile_conflict"],
                    "Field observation not found": c["report_target_missing"],
                }
                if detail in translations:
                    return translations[detail]
                return detail if language == "en" else c["request_error"]
            if isinstance(detail, list):
                locations = {str(item.get("loc", [""])[-1]): item.get("type", "") for item in detail if isinstance(item, dict)}
                if "password" in locations:
                    return c["password_min_error"]
                if "display_name" in locations:
                    return c["username_invalid"]
                if "email" in locations:
                    return c["email_invalid"]
                messages = [str(item.get("msg", "")) for item in detail if isinstance(item, dict) and item.get("msg")]
                if messages:
                    return " ".join(messages)
        except (ValueError, AttributeError):
            pass
    return c["request_error"]


def _show_request_error(exc: requests.RequestException, language: str, key: str) -> None:
    st.error(_error_message(exc, language))
    if st.button(COPY.get(language, COPY["en"])["community_retry"], key=key, use_container_width=True):
        st.rerun()


@error_boundary("Farmer Community")
def render_community() -> None:
    st.markdown('''<style>@media(max-width:700px){.block-container{padding:1rem .8rem 3rem!important}[data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button{min-height:3rem;width:100%}[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea{font-size:16px}}</style>''', unsafe_allow_html=True)
    language = get_current_language()
    if language not in COPY:
        language = "en"
    c = COPY[language]

    # 1. Process Google OAuth callback query parameters
    google_code = st.query_params.get("community_google_code")
    if google_code:
        browser_binding = st.context.cookies.get("community_google_handoff", "")
        if not browser_binding:
            st.query_params.pop("community_google_code", None)
            st.error(c["google_error_expired"])
        else:
            try:
                response = _request(
                    "POST",
                    "/community/auth/google/exchange",
                    payload={"code": google_code, "browser_binding": browser_binding},
                )
                _store_community_session(response)
                st.query_params.pop("community_google_code", None)
                st.switch_page("Home.py")
            except requests.RequestException as exc:
                st.query_params.pop("community_google_code", None)
                st.error(_error_message(exc, language))

    google_error = st.query_params.get("community_google_error")
    if google_error:
        error_key = f"google_error_{google_error}"
        st.error(c.get(error_key, c["google_error_generic"]))
        st.query_params.pop("community_google_error", None)

    # 2. Process Email Verification query parameters
    verify_token = st.query_params.get("community_verify_token") or st.query_params.get("verify_token")
    if verify_token:
        try:
            _request("POST", "/community/email/verify", payload={"token": verify_token})
            st.session_state["community_email_verified"] = True
            st.query_params.pop("community_verify_token", None)
            st.query_params.pop("verify_token", None)
            st.rerun()
        except requests.RequestException as exc:
            st.query_params.pop("community_verify_token", None)
            st.query_params.pop("verify_token", None)
            st.error(_error_message(exc, language))

    if st.session_state.pop("community_email_verified", False):
        st.success(c["verify_success"])

    # 3. Process Password Reset query parameters
    reset_token = st.query_params.get("community_reset_token") or st.query_params.get("reset_token")
    if reset_token:
        from components.cards import centralized_login_container, login_card_header, security_trust_footer
        with centralized_login_container():
            login_card_header(
                title=c["reset_password"],
                subtitle=c["reset_link_subtitle"],
                badge_text="SECURITY RECOVERY",
                accent_color="#10b981",
            )
            with st.form("community_password_reset_form"):
                new_password = st.text_input(c["reset_password"], type="password", key="community_new_password")
                confirmation = st.text_input(c["confirm_password"], type="password", key="community_confirm_password")
                submit_reset = st.form_submit_button(c["save_password"], type="primary", use_container_width=True)
            if submit_reset:
                if len(new_password) < 12:
                    st.error(c["password_min_error"])
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
            security_trust_footer()
        return

    if st.session_state.pop("community_reset_success", False):
        st.success(c["password_updated"])

    # 4. Session Expiry Check
    community_token = st.session_state.get("community_access_token")
    community_expiry = st.session_state.get("community_access_token_expires_at")
    if community_token and (community_expiry is not None and time.time() >= community_expiry):
        _clear_community_session(expired=True)
    if st.session_state.pop("community_session_expired", False):
        st.info(c["session_expired"])

    # 5. Unauthenticated State: Centralized Executive Login Card
    if not st.session_state.get("community_access_token"):
        from components.cards import centralized_login_container, login_card_header, security_trust_footer
        st.markdown(
            """
            <style>
            .st-key-ag_centralized_login_col {
                box-sizing: border-box !important;
                width: min(100%, 340px) !important;
                max-width: 340px !important;
                margin: 0.35rem auto 1rem !important;
                padding: 0.75rem 0.9rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stVerticalBlock"] {
                gap: 0.4rem !important;
            }
            .st-key-ag_centralized_login_col .ag-login-icon-box,
            .st-key-ag_centralized_login_col .ag-login-icon-box + span,
            .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div[style*="height: 1px"] {
                display: none !important;
            }
            .st-key-ag_centralized_login_col h2 {
                margin: 0 0 0.15rem !important;
                color: #172338 !important;
                font-size: 1.05rem !important;
                font-weight: 700 !important;
                letter-spacing: 0 !important;
            }
            .st-key-ag_centralized_login_col h2 + p {
                margin: 0 !important;
                color: #718198 !important;
                font-size: 0.55rem !important;
                line-height: 1.35 !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stCaptionContainer"] {
                display: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a {
                box-sizing: border-box !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 0.5rem !important;
                min-height: 2rem !important;
                padding: 0.25rem 0.55rem !important;
                border: 1px solid #e1e8f0 !important;
                border-radius: 8px !important;
                background: #ffffff !important;
                color: #253247 !important;
                font-size: 0.55rem !important;
                font-weight: 600 !important;
                box-shadow: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div[style*="display:flex"][style*="align-items:center"] {
                gap: 0.5rem !important;
                margin: 0.2rem 0 !important;
                font-size: 0.55rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tablist"] {
                display: flex !important;
                width: 100% !important;
                gap: 0 !important;
                padding: 0 !important;
                border: 1px solid #e4ebf3 !important;
                border-radius: 7px !important;
                background: #f4f7fb !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"] {
                flex: 1 1 50% !important;
                justify-content: center !important;
                min-height: 1.55rem !important;
                padding: 0.25rem 0.35rem !important;
                border: 0 !important;
                border-radius: 6px !important;
                background: transparent !important;
                color: #64748b !important;
                font-size: 0.5rem !important;
                font-weight: 500 !important;
                box-shadow: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
                color: #0875d1 !important;
                border-bottom: 1px solid #328ff0 !important;
                background: #ffffff !important;
                box-shadow: 0 2px 6px rgba(50, 143, 240, 0.12) !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stWidgetLabel"] p {
                color: #172338 !important;
                font-size: 0.55rem !important;
                font-weight: 600 !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {
                box-sizing: border-box !important;
                min-height: 1.75rem !important;
                padding: 0.25rem 0.55rem !important;
                border: 1px solid #e1e8f0 !important;
                border-radius: 7px !important;
                background: #ffffff !important;
                color: #253247 !important;
                font-size: 0.55rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTextInput"] input::placeholder {
                color: #98a3b3 !important;
                opacity: 1 !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stForm"] {
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
            }
            .st-key-community_login_password [data-testid="stTextInput"] button,
            .st-key-community_register_password [data-testid="stTextInput"] button {
                min-width: 2.4rem !important;
                padding: 0 0.2rem !important;
                background: transparent !important;
                box-shadow: none !important;
            }
            .st-key-community_login_password [data-testid="stTextInput"] button span[data-testid="stIconMaterial"],
            .st-key-community_register_password [data-testid="stTextInput"] button span[data-testid="stIconMaterial"] {
                font-size: 0.65rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stFormSubmitButton"] button {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-height: 2.1rem !important;
                border: 0 !important;
                border-radius: 999px !important;
                background: #328ff0 !important;
                color: #ffffff !important;
                font-size: 0.6rem !important;
                font-weight: 700 !important;
                box-shadow: 0 6px 16px rgba(50, 143, 240, 0.18) !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stPopover"] button {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-height: 1.45rem !important;
                margin-top: 0.2rem !important;
                padding: 0.15rem 0.4rem !important;
                border: 0 !important;
                border-top: 0 !important;
                border-bottom: 0 !important;
                border-radius: 0 !important;
                background: linear-gradient(#e1e8f0, #e1e8f0) center / 100% 1px no-repeat !important;
                color: #0875d1 !important;
                font-size: 0.5rem !important;
                box-shadow: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
                display: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stPopover"] button p {
                padding: 0 0.25rem !important;
                background: #ffffff !important;
                font-size: inherit !important;
            }
            .st-key-community_verification_resend_popover [data-testid="stPopover"] button {
                justify-content: space-between !important;
                min-height: 1.9rem !important;
                margin-top: 0.15rem !important;
                padding: 0.25rem 0.55rem !important;
                border: 1px solid #e1e8f0 !important;
                border-radius: 8px !important;
                background: #ffffff !important;
                color: #34445a !important;
            }
            .st-key-community_verification_resend_popover [data-testid="stPopover"] button p {
                margin-right: auto !important;
                background: transparent !important;
            }
            @media (max-width: 700px) {
                .st-key-ag_centralized_login_col {
                    width: min(100%, 340px) !important;
                    padding: 0.75rem 0.9rem !important;
                    border-radius: 10px !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {
                    min-height: 1.75rem !important;
                    font-size: 0.55rem !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <style>
            .st-key-ag_centralized_login_col {
                width: min(100%, 360px) !important;
                max-width: 360px !important;
                padding: 0.9rem 1rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stVerticalBlockBorderWrapper"] {
                width: 100% !important;
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                border: 1px solid #e1e7ef !important;
                border-radius: 10px !important;
                background: #ffffff !important;
                box-shadow: 0 4px 16px rgba(27, 57, 91, 0.05) !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stVerticalBlock"] {
                gap: 0.55rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stWidgetLabel"] p {
                color: #14264a !important;
                font-size: 0.72rem !important;
                font-weight: 600 !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {
                min-height: 1.9rem !important;
                padding: 0.25rem 0.7rem !important;
                border: 1px solid #c9dcfb !important;
                border-radius: 999px !important;
                background: #ffffff !important;
                color: #253247 !important;
                font-size: 0.72rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTextInput"] input:focus {
                border-color: #c9dcfb !important;
                outline: none !important;
                box-shadow: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a {
                min-height: 2rem !important;
                padding: 0.3rem 0.7rem !important;
                border: 1px solid #b9d3fb !important;
                border-radius: 999px !important;
                background: #ffffff !important;
                color: #14264a !important;
                font-size: 0.72rem !important;
                font-weight: 650 !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a::before {
                content: "G";
                font: 700 0.95rem/1 Arial, sans-serif;
                background: conic-gradient(#4285f4 0 25%, #34a853 25% 50%, #fbbc05 50% 75%, #ea4335 75%);
                background-clip: text;
                -webkit-background-clip: text;
                color: transparent;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tablist"] {
                gap: 0 !important;
                padding: 0.12rem !important;
                border: 0 !important;
                border-radius: 999px !important;
                background: #edf3fc !important;
                box-shadow: 0 2px 6px rgba(38, 91, 158, 0.08) !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"] {
                flex: 1 1 50% !important;
                justify-content: center !important;
                min-height: 2rem !important;
                padding: 0.3rem 0.45rem !important;
                border: 0 !important;
                border-radius: 999px !important;
                background: transparent !important;
                color: #14264a !important;
                font-size: 0.72rem !important;
                font-weight: 600 !important;
                box-shadow: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"]::after {
                display: none !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
                border: 0 !important;
                background: linear-gradient(135deg, #3394ff, #0875d1) !important;
                color: #ffffff !important;
                box-shadow: 0 3px 8px rgba(8, 117, 209, 0.2) !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"][aria-selected="true"] * {
                color: #ffffff !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stForm"] {
                padding: 0 !important;
                border: 0 !important;
                background: transparent !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stFormSubmitButton"] button {
                min-height: 2.05rem !important;
                border: 0 !important;
                border-radius: 999px !important;
                background: linear-gradient(135deg, #3394ff, #0875d1) !important;
                color: #ffffff !important;
                font-size: 0.74rem !important;
                font-weight: 700 !important;
                box-shadow: 0 5px 12px rgba(8, 117, 209, 0.2) !important;
            }
            .st-key-community_login_password [data-testid="stTextInput"] button,
            .st-key-community_register_password [data-testid="stTextInput"] button {
                min-width: 2.7rem !important;
                padding: 0 0.3rem !important;
            }
            .st-key-community_login_password [data-testid="stTextInput"] button::after,
            .st-key-community_register_password [data-testid="stTextInput"] button::after {
                font-size: 0.62rem !important;
            }
            .st-key-community_forgot_password_popover [data-testid="stPopover"] button {
                min-height: 1.55rem !important;
                margin-top: 0 !important;
                padding: 0.15rem 0.4rem !important;
                border: 0 !important;
                border-radius: 999px !important;
                background: transparent !important;
                color: #0875d1 !important;
                font-size: 0.7rem !important;
                box-shadow: none !important;
            }
            .st-key-community_forgot_password_popover [data-testid="stPopover"] button::after {
                display: none !important;
            }
            .st-key-community_verification_resend_popover [data-testid="stPopover"] button {
                min-height: 1.95rem !important;
                margin-top: 0.1rem !important;
                padding: 0.25rem 0.65rem !important;
                border: 1px solid #b9d3fb !important;
                border-radius: 999px !important;
                background: #ffffff !important;
                color: #14264a !important;
                font-size: 0.68rem !important;
            }
            .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div[style*="Administrator or agronomist?"] {
                margin-top: 0.35rem !important;
                color: #14264a !important;
                font-size: 0.62rem !important;
            }
            @media (max-width: 700px) {
                .st-key-ag_centralized_login_col {
                    width: min(100%, 360px) !important;
                    padding: 0.8rem 0.85rem !important;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        with centralized_login_container(max_width=620):
            st.markdown(
                """
                <style>
                body:has(.st-key-ag_centralized_login_col) .st-key-ag_desktop_navbar,
                body:has(.st-key-ag_centralized_login_col) .st-key-ag_mobile_navbar,
                body:has(.st-key-ag_centralized_login_col) .ag-nav-rule {
                    display: none !important;
                }
                body:has(.st-key-ag_centralized_login_col) .block-container,
                body:has(.st-key-ag_centralized_login_col) [data-testid="stMainBlockContainer"] {
                    padding-top: 0.15rem !important;
                    padding-bottom: 0 !important;
                }
                .st-key-ag_centralized_login_col.st-key-ag_centralized_login_col {
                    box-sizing: border-box !important;
                    width: min(100%, 360px) !important;
                    max-width: 360px !important;
                    min-height: 0 !important;
                    height: auto !important;
                    margin: 0 auto !important;
                    padding: 0.45rem 0.8rem !important;
                    border: 0 !important;
                    border-radius: 0 !important;
                    background: transparent !important;
                    box-shadow: none !important;
                    justify-content: flex-start !important;
                }
                .st-key-ag_centralized_login_col.st-key-ag_centralized_login_col [data-testid="stVerticalBlockBorderWrapper"] {
                    width: 100% !important;
                    max-width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    border: 0 !important;
                    background: transparent !important;
                    box-shadow: none !important;
                }
                .st-key-ag_centralized_login_col.st-key-ag_centralized_login_col [data-testid="stVerticalBlock"] {
                    gap: 0.22rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div:has(> .ag-login-icon-box) {
                    display: none !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div[style*="display:flex"][style*="align-items:center"] {
                    gap: 0.45rem !important;
                    margin: 0.3rem 0 !important;
                    font-size: 0.72rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTabs"] {
                    gap: 0 !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTabPanel"] {
                    padding: 0.1rem 0 0 !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stForm"] [data-testid="stVerticalBlock"] {
                    gap: 0.18rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {
                    min-height: 1.55rem !important;
                    padding-top: 0.15rem !important;
                    padding-bottom: 0.15rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stFormSubmitButton"] button {
                    min-height: 1.7rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a {
                    min-height: 1.75rem !important;
                    padding-top: 0.15rem !important;
                    padding-bottom: 0.15rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"] {
                    min-height: 1.7rem !important;
                    padding-top: 0.15rem !important;
                    padding-bottom: 0.15rem !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stPopover"] button {
                    min-height: 1.45rem !important;
                    margin-top: 0 !important;
                }
                .st-key-ag_centralized_login_col [data-testid="stMarkdownContainer"] div[style*="Administrator or agronomist?"] {
                    margin-top: 0 !important;
                    font-size: 0.62rem !important;
                }
                @media (max-height: 900px) {
                    .st-key-ag_centralized_login_col.st-key-ag_centralized_login_col {
                        padding: 0.35rem 0.7rem !important;
                    }
                    .st-key-ag_centralized_login_col.st-key-ag_centralized_login_col [data-testid="stVerticalBlock"] {
                        gap: 0.16rem !important;
                    }
                    .st-key-ag_centralized_login_col [data-testid="stTextInput"] input {
                        min-height: 1.45rem !important;
                    }
                    .st-key-ag_centralized_login_col [data-testid="stLinkButton"] a,
                    .st-key-ag_centralized_login_col [data-testid="stTabPanel"] [data-testid="stFormSubmitButton"] button {
                        min-height: 1.55rem !important;
                    }
                    .st-key-ag_centralized_login_col [data-testid="stTabs"] [role="tab"] {
                        min-height: 1.5rem !important;
                    }
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            sprout_icon = """<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 20h10"/>
                <path d="M10 20c0-4 1-6 2-10"/>
                <path d="M12 10a4 4 0 0 1 7-3 4 4 0 0 1-3 7 4 4 0 0 1-4-4z"/>
                <path d="M12 14a4 4 0 0 0-7-3 4 4 0 0 0 3 7 4 4 0 0 0 4-4z"/>
            </svg>"""
            badge_title = "GROWER NETWORK" if language == "en" else "UMURYANGO W'ABAHINZI" if language == "rw" else "RÉSEAU AGRICOLE"
            login_card_header(
                title=c["welcome_back"],
                subtitle=c["signin_subtitle"],
                badge_text=badge_title,
                icon=sprout_icon,
                accent_color="#10b981",
                title_color="#14264a",
                title_font_size="1.1rem",
                subtitle_color="#405477",
                subtitle_font_size="0.72rem",
                text_align="center",
            )
            if _google_sign_in_enabled():
                st.link_button(
                    c["google_signin"],
                    "/community/auth/google",
                    use_container_width=True,
                )
                st.caption(c["google_new_account_note"])
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:1rem;margin:1rem 0;color:#64748b;font-size:1rem;"><span style="height:1px;flex:1;background:#dce5ef;"></span><span>{c.get("email_separator", "or sign in with email")}</span><span style="height:1px;flex:1;background:#dce5ef;"></span></div>',
                    unsafe_allow_html=True,
                )

            sign_in, create_account = st.tabs([c["signin"], c["create"]])
            with sign_in:
                with st.form("community_sign_in"):
                    email = st.text_input(c["email"], placeholder="farmer@cooperative.rw", key="community_login_email")
                    password = st.text_input(c["password"], type="password", placeholder="••••••••••••", key="community_login_password")
                    submit = st.form_submit_button(
                        c["signin"], type="primary", use_container_width=True,
                        disabled=st.session_state.get("community_login_running", False),
                    )
                if submit:
                    st.session_state["community_login_running"] = True
                    try:
                        response = _request("POST", "/community/login", payload={"email": email, "password": password})
                        _store_community_session(response)
                        st.switch_page("Home.py")
                    except requests.RequestException as exc:
                        _show_request_error(exc, language, "community_login_retry")
                    finally:
                        st.session_state["community_login_running"] = False

                with st.popover(c["forgot_password"], use_container_width=True, key="community_forgot_password_popover"):
                    with st.form("community_password_forgot_form"):
                        reset_email = st.text_input(c["email"], key="community_reset_email")
                        send_reset = st.form_submit_button(c["send_reset"])
                    if send_reset:
                        try:
                            reset_result = _request("POST", "/community/password/forgot", payload={"email": reset_email})
                            st.success(c["reset_requested"])
                            if reset_result.get("development_reset_url"):
                                _show_development_mail_status(reset_result, language)
                                st.link_button(c["reset_dev_link"], reset_result["development_reset_url"], type="primary")
                            elif reset_result.get("development_error"):
                                st.warning(c["reset_dev_error"])
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))

                with st.popover(
                    c["verify_resend"],
                    use_container_width=True,
                    key="community_verification_resend_popover",
                ):
                    st.caption(c["verify_resend_help"])
                    with st.form("community_verification_resend"):
                        verify_email = st.text_input(c["email"], key="community_verify_email_input")
                        resend = st.form_submit_button(c["verify_resend"])
                    if resend:
                        try:
                            verify_result = _request("POST", "/community/email/verification/resend", payload={"email": verify_email})
                            st.success(c["verify_sent"])
                            if verify_result.get("development_verification_url"):
                                _show_development_mail_status(verify_result, language)
                                st.link_button(c["verify_dev_link"], verify_result["development_verification_url"])
                            elif verify_result.get("development_error"):
                                st.warning(c["verify_dev_error"])
                        except requests.RequestException as exc:
                            st.error(_error_message(exc, language))

            with create_account:
                with st.form("community_register"):
                    display_name = st.text_input(c["name"], placeholder="e.g. Jean_Gasabo", max_chars=80)
                    email = st.text_input(c["email"], placeholder="farmer@cooperative.rw", key="community_register_email")
                    password = st.text_input(
                        c["password"] + f" ({c['password_minimum']})",
                        type="password",
                        placeholder=c["password_minimum"],
                        key="community_register_password",
                    )
                    submit = st.form_submit_button(c["create_farmer"], type="primary", use_container_width=True)
                if submit:
                    try:
                        response = _request("POST", "/community/register", payload={
                            "display_name": display_name, "email": email, "password": password,
                        })
                        st.success(c["register_sent"])
                        if response.get("development_verification_url"):
                            _show_development_mail_status(response, language)
                            st.link_button(c["verify_dev_link"], response["development_verification_url"])
                        if response.get("access_token"):
                            _store_community_session(response)
                            st.switch_page("Home.py")
                    except requests.RequestException as exc:
                        st.error(_error_message(exc, language))

            st.markdown(
                f'<div style="text-align:center;margin-top:0.35rem;font-size:0.48rem;color:#94a3b8;">{c["admin_portal_link"]} <a href="/Admin" style="color:#0875d1;font-weight:700;text-decoration:none;">→</a></div>',
                unsafe_allow_html=True,
            )
        return

    # 6. Authenticated Community State
    st.title(c["title"])
    st.write(c["intro"])
    st.caption(c["warning"])

    account = st.session_state.get("community_account", {})
    from components.cards import authenticated_session_badge
    display_name = account.get('display_name') or c['reply_author']
    email = account.get('email', '')
    if authenticated_session_badge(display_name=display_name, email=email, role=c['farmer'], key_prefix="community"):
        _clear_community_session()
        st.rerun()

    with st.popover(c["profile_title"]):
        st.caption(c["profile_help"])
        with st.form("community_profile_update"):
            updated_name = st.text_input(
                c["profile_username"], value=display_name, max_chars=30,
                key="community_profile_display_name",
            )
            profile_submit = st.form_submit_button(c["save_profile"], type="primary")
        if profile_submit:
            try:
                result = _request(
                    "PATCH", "/community/profile",
                    payload={"display_name": updated_name.strip()},
                )
                st.session_state["community_account"] = {
                    **account, **result.get("account", {}),
                }
                st.session_state["community_profile_saved"] = True
                st.rerun()
            except requests.RequestException as exc:
                st.error(_error_message(exc, language))
    if st.session_state.pop("community_profile_saved", False):
        st.success(c["profile_saved"])

    try:
        notifications = _request("GET", "/community/notifications")
    except requests.RequestException as exc:
        st.error(_error_message(exc, language))
    else:
        with st.expander(
            f"{c['notification_title']} ({len(notifications)})",
            expanded=bool(notifications),
        ):
            if not notifications:
                st.caption(c["notification_empty"])
            for notification in notifications:
                post = notification.get("post") or {}
                st.write(c["notification_item"].format(
                    actor=notification.get("actor_display_name", c["reply_author"]),
                    title=post.get("title", c["new_post"]),
                ))
            if notifications and st.button(
                c["mark_notifications_read"], key="community_notifications_read",
            ):
                try:
                    _request("POST", "/community/notifications/read")
                    st.session_state["community_notifications_marked_read"] = True
                    st.rerun()
                except requests.RequestException as exc:
                    st.error(_error_message(exc, language))
    if st.session_state.pop("community_notifications_marked_read", False):
        st.success(c["notification_read"])

    # WhatsApp Bot Access Banner
    try:
        whatsapp_info = request_api(
            "GET", "/communication/whatsapp-info", timeout=5
        )
        whatsapp_info.raise_for_status()
        wa_data = whatsapp_info.json()
        if wa_data.get("enabled"):
            with st.container(border=True):
                st.markdown(f"**{c['wa_title']}**")
                st.write(c["wa_intro"])
                st.caption(c["wa_commands"])
                wa_url = wa_data.get("chat_url") or (
                    f"https://wa.me/{wa_data.get('phone_e164', '').lstrip('+')}"
                    if wa_data.get("phone_e164") else None
                )
                if wa_url:
                    st.link_button(c["wa_open"], wa_url)
        else:
            st.info(c["wa_pending"])
    except requests.RequestException:
        st.info(c["wa_unavailable"])

    selected_section = st.radio(
        c["title"], [c["discussion_tab"], c["field_tab"]],
        horizontal=True, label_visibility="collapsed", key="community_feed_section",
    )
    if selected_section == c["field_tab"]:
        _field_reports(st.session_state["community_access_token"], language)
    else:
        with st.container(border=True):
            st.subheader(c["new_post"])
            with st.form("community_new_post", clear_on_submit=True):
                body = st.text_area(c["post_body"], max_chars=5000, height=130, placeholder=c["post_body_hint"])
                title = st.text_input(c["topic"], max_chars=140, placeholder=c["topic_hint"])
                submit = st.form_submit_button(c["publish"], type="primary", use_container_width=True)
            if submit:
                if not body.strip():
                    st.warning(c["write_before_posting"])
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
            c["discussion_search"], placeholder=c["discussion_search_hint"],
            key="community_feed_search",
        ).strip().casefold()
        if feed_search:
            posts = [post for post in posts if feed_search in " ".join((
                str(post.get("title") or ""), str(post.get("body") or ""),
                str((post.get("author") or {}).get("display_name") or ""),
            )).casefold()]
            st.caption(c["discussion_search_scope"])

        if not posts:
            st.info(c["discussion_no_match"] if feed_search else c["empty"])

        comments_by_post = {}
        if posts:
            try:
                comments = _community_comments_for_posts(
                    posts, st.session_state["community_access_token"]
                )
                for comment in comments:
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
                        if str(comment.get("author_id")) != str(account.get("id")):
                            with st.popover(c["report_content"]):
                                with st.form(f"report_comment_{comment.get('id')}"):
                                    reason = st.text_input(c["report_reason"], max_chars=500)
                                    report_comment = st.form_submit_button(c["send_to_admins"])
                                if report_comment:
                                    if len(reason.strip()) < 3:
                                        st.warning(c["report_required"])
                                    else:
                                        try:
                                            _request(
                                                "POST", f"/community/posts/{post_id}/report",
                                                payload={"reason": reason.strip(), "comment_id": comment["id"]},
                                            )
                                            st.success(c["report_sent_confirmation"])
                                        except requests.RequestException as exc:
                                            st.error(_error_message(exc, language))
                with st.form(f"community_comment_{post_id}", clear_on_submit=True):
                    reply = st.text_area(c["reply"], max_chars=1500, key=f"reply_{post_id}")
                    reply_submit = st.form_submit_button(c["send_reply"], type="primary")
                if reply_submit:
                    if not reply.strip():
                        st.warning(c["write_before_reply"])
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
                    with action_cols[0].popover(c["report_content"]):
                        with st.form(f"report_post_{post_id}"):
                            reason = st.text_input(c["report_reason"], max_chars=500)
                            report = st.form_submit_button(c["send_to_admins"])
                        if report:
                            if len(reason.strip()) < 3:
                                st.warning(c["report_required"])
                            else:
                                try:
                                    _request("POST", f"/community/posts/{post_id}/report", payload={"reason": reason.strip()})
                                    st.success(c["report_sent_confirmation"])
                                except requests.RequestException as exc:
                                    st.error(_error_message(exc, language))

        page_cols = st.columns([1, 1, 4])
        with page_cols[0]:
            if feed_offset > 0 and st.button(c["newer_posts"], key="community_feed_newer"):
                st.session_state["community_feed_offset"] = max(0, feed_offset - 15)
                st.rerun()
        with page_cols[1]:
            if page_post_count == 15 and st.button(c["older_posts"], key="community_feed_older"):
                st.session_state["community_feed_offset"] = feed_offset + 15
                st.rerun()
