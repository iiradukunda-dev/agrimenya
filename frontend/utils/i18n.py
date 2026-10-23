"""
Internationalization (i18n) module for agrimenya.
Provides multi-language support for English (EN), Kinyarwanda (RW), and French (FR)
using a professional GNU gettext architecture and a robust LocalizationManager class.
Strictly complies with project rules: no emojis, clean modular structure, type hinting.
"""
import gettext
import logging
import os
from typing import Dict, Any, Optional

import streamlit as st

logger = logging.getLogger(__name__)

LANGUAGES = {
    "en": "en",
    "rw": "rw",
    "fr": "fr",
}

DEFAULT_LANGUAGE = "en"

# Custom fallback dictionary in case .mo files are missing
FALLBACK_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "common.language": "Language",
        "common.all_regions": "All Regions",
        "common.crop": "Crop",
        "common.district": "District",
        "common.status": "Status",
        "common.pending": "Pending",
        "common.unknown_area": "Unknown Area",
        "common.unknown_crop": "Unknown Crop",
        "common.unknown_task": "Unknown Task",
        "common.built_for": "Built for the 2026 NISR Big Data Hackathon",
        "priority.high": "High",
        "priority.medium": "Medium",
        "priority.low": "Low",
        "home.app_title": "agrimenya",
        "home.subtitle": "Decision and Planning Support System for Agricultural Productivity",
        "home.welcome": "Welcome to **agrimenya**. This platform empowers planners, extension officers, and cooperative leaders with data-driven insights using SAS, AHS, and EICV7 datasets.",
        "home.kpi.farmers": "Total Farmers Supported",
        "home.kpi.yield": "Avg Yield Increase",
        "home.kpi.cooperatives": "Active Cooperatives",
        "home.pillars_title": "Core Pillars",
        "pillar.segmentation.title": "Segment",
        "pillar.segmentation.desc": "Identify high-priority zones based on yield and risk data.",
        "pillar.segmentation.btn": "Segment",
        "pillar.decisions.title": "Decide",
        "pillar.decisions.desc": "Review ranked priorities, evidence, and planned actions.",
        "pillar.decisions.btn": "Decide",
        "pillar.planification.title": "Plan",
        "pillar.planification.desc": "Plan and track agricultural roadmaps and execution.",
        "pillar.planification.btn": "Plan",
        "pillar.communication.title": "Communicate",
        "pillar.communication.desc": "Share alerts, plans, and coordinate with stakeholders.",
        "pillar.communication.btn": "Communicate",
        "decisions.page_title": "Decision Making",
        "decisions.header": "Decision Making",
        "decisions.subtitle": "District crop evidence for planning and follow-up.",
        "decisions.empty": "No recommendations currently available or the backend could not be reached.",
        "decisions.act_btn": "Act",
        "decisions.role_note": "Decide presents structured assessments from available data. For open questions and plain-language explanations, use AI Assistant.",
        "decisions.priority_item": "Priority {number}",
        "decisions.no_detail": "No supporting recommendation detail is available for this item.",
        "decisions.evidence_title": "Evidence to consider",
        "decisions.evidence_note": "Use recent field observations as context alongside the structured priorities. Community reports are not verified statistics or advice.",
        "decisions.zone_context": "Select an area",
        "decisions.zone_required": "Add or load an area to review its recent field observations.",
        "decisions.ask_assistant": "Ask AI Assistant to explain this evidence",
        "decisions.field_signal": "Recent farmer observations (last 30 days)",
        "decisions.field_signal_note": "Community observations are an early field signal, not verified advice or official NISR data. They do not change the historical yield baseline.",
        "decisions.field_signal_empty": "No farmer observations recorded in this zone during the last 30 days.",
        "decisions.field_signal_metric": "Reported field signal",
        "decisions.field_signal_count": "{count} observations",
        "decisions.field_signal_unavailable": "Field observations are temporarily unavailable.",
        "plan.page_title": "Planification",
        "plan.header": "Planification",
        "plan.subtitle": "Roadmaps and execution timelines for agricultural interventions.",
        "plan.context_header": "Plan Context",
        "plan.select_zone": "Select Zone",
        "plan.season": "Season",
        "plan.season_a": "Season A",
        "plan.season_b": "Season B",
        "plan.season_c": "Season C",
        "plan.zone_all": "All Regions",
        "plan.zone_north": "Northern Province",
        "plan.zone_east": "Eastern Province",
        "plan.zone_south": "Southern Province",
        "plan.zone_west": "Western Province",
        "plan.roadmap_title": "Execution Roadmap: {zone} ({season})",
        "plan.empty": "No roadmap data available for the selected criteria.",
        "plan.chart_title": "Intervention Schedule",
        "plan.detailed_steps": "Detailed Steps",
        "plan.due": "Due",
        "plan.save_btn": "Save & Share Plan",
        "plan.phase.preparation": "Preparation",
        "plan.phase.execution": "Execution",
        "plan.phase.monitoring": "Monitoring",
        "plan.task.seeds": "Procure Seeds",
        "plan.task.fertilizer": "Distribute Fertilizer",
        "plan.task.training": "Planting Training",
        "plan.task.monitoring": "Monitoring",
        "seg.page_title": "Segmentation",
        "seg.header": "Agricultural Segmentation",
        "seg.subtitle": "Compare observed crop production across Rwanda’s districts and seasons.",
        "seg.filters": "Filters",
        "seg.season": "Season",
        "seg.crops": "Crops",
        "seg.priority_level": "Priority Level",
        "seg.empty": "No data available. Please check the backend connection.",
        "seg.map_title": "Priority Zones Map",
        "seg.yield_title": "Yield Analysis",
        "seg.chart_title": "Estimated Production by District and Priority",
        "seg.axis_district": "District",
        "seg.axis_yield": "Estimated Production (MT)",
        "seg.summary_title": "Zoning Summary",
        "seg.col_district": "District",
        "seg.col_crop": "Crop",
        "seg.col_priority": "Priority",
        "seg.col_yield": "Estimated Production (MT)",
        "comm.page_title": "Communication",
        "comm.header": "Efficient Communication",
        "comm.subtitle": "Real-time alerts, updates, and coordination across stakeholders.",
        "comm.feed_title": "Alert Feed",
        "comm.feed_empty": "No new alerts or the backend could not be reached.",
        "comm.share_title": "Share Information",
        "comm.target_audience": "Target Audience",
        "comm.audience.extension": "Extension Officers",
        "comm.audience.coop": "Cooperative Leaders",
        "comm.audience.planners": "Government Planners",
        "comm.audience.all": "All Stakeholders",
        "comm.message_label": "Message / Announcement",
        "comm.is_urgent": "Mark as Urgent",
        "comm.send_btn": "Send Update",
        "comm.success": "Message sent to {group}!",
        "comm.error_empty": "Please enter a message.",
        "comm.alert_type.warning": "Warning",
        "comm.alert_type.info": "Info",
        "comm.alert_type.urgent": "Urgent",
        "error.404.title": "Page Not Found",
        "error.404.desc": "The page you are looking for does not exist or has been moved.",
        "error.network.title": "Network Error",
        "error.network.desc": "Failed to connect to the backend server. Please check your connection and try again.",
        "error.validation.title": "Validation Error",
        "error.validation.desc": "The data provided is invalid. Please review your inputs.",
        "error.system.title": "System Error",
        "error.system.desc": "An unexpected system error occurred. Our team has been notified.",
        "error.go_home": "Return to Home",
    },
    "rw": {
        "common.language": "Ururimi",
        "common.all_regions": "Intara Zose",
        "common.crop": "Igihingwa",
        "common.district": "Akarere",
        "common.status": "Imiterere",
        "common.pending": "Birategerejwe",
        "common.unknown_area": "Agace Katazwi",
        "common.unknown_crop": "Igihingwa Katazwi",
        "common.unknown_task": "Igikorwa Kitazwi",
        "common.built_for": "Byakozwe ku bwa NISR Big Data Hackathon ya 2026",
        "priority.high": "Ikomeye",
        "priority.medium": "Iringaniye",
        "priority.low": "Iri Hasi",
        "home.app_title": "agrimenya",
        "home.subtitle": "Sisitemu yo Gufata Ibyemezo no Gutegura Umusaruro w'Ubuhinzi",
        "home.welcome": "Murakaza neza kuri **agrimenya**. Uru rubuga rufasha abategura igenamigambi, abashinzwe ubuhinzi, n'abayobozi b'amakoperative gufata ibyemezo bishingiye ku makuru ya SAS, AHS, na EICV7.",
        "home.kpi.farmers": "Abahinzi Bose Bafashijwe",
        "home.kpi.yield": "Impuzandengo y'Ukwiyongera k'Umusaruro",
        "home.kpi.cooperatives": "Amakoperative Akora",
        "home.pillars_title": "Inkingi z'Ingenzi",
        "pillar.segmentation.title": "Iteganyazoni",
        "pillar.segmentation.desc": "Kumenya uduce tw'ibanze dushingiye ku musaruro n'ibyago.",
        "pillar.segmentation.btn": "Gana ku Iteganyazoni",
        "pillar.decisions.title": "Gufata Ibyemezo",
        "pillar.decisions.desc": "Gusuzuma ibyihutirwa, ibimenyetso bibishyigikira, n'ibikorwa biteganyijwe.",
        "pillar.decisions.btn": "Gana ku Byemezo",
        "pillar.planification.title": "Igenamigambi",
        "pillar.planification.desc": "Gutebya no gukurikirana igenamigambi ry'ubuhinzi n'ishyirwa mu bikorwa.",
        "pillar.planification.btn": "Gana ku Igenamigambi",
        "pillar.communication.title": "Itumanaho",
        "pillar.communication.desc": "Gusangiza integuza, igenamigambi, no guhuza ibikorwa by'abafatanyabikorwa.",
        "pillar.communication.btn": "Gana ku Itumanaho",
        "decisions.page_title": "Gufata Ibyemezo",
        "decisions.header": "Gufata Ibyemezo",
        "decisions.subtitle": "Amakuru y'akarere ku bihingwa yo gufasha mu igenamigambi no gukurikirana.",
        "decisions.empty": "Nta inama zibonetse ubu cyangwa seriveri ntiri kuboneka.",
        "decisions.act_btn": "Gira icyo ukora",
        "decisions.role_note": "Iki gice kigaragaza isuzuma rishingiye ku makuru ahari. Ku bibazo bisanzwe no gusobanurirwa mu magambo yoroshye, koresha AI Assistant.",
        "decisions.priority_item": "Icyihutirwa {number}",
        "decisions.no_detail": "Nta bisobanuro by'inyongera bihari kuri iki cyifuzo.",
        "decisions.evidence_title": "Ibimenyetso byo kwitaho",
        "decisions.evidence_note": "Reba amakuru mashya yo mu mirima nk'inyongera ku isuzuma. Amakuru y'abaturage si imibare yemejwe cyangwa inama zemewe.",
        "decisions.zone_context": "Hitamo agace",
        "decisions.zone_required": "Ongeraho cyangwa ufungure agace kugira ngo urebe amakuru mashya yo mu murima.",
        "decisions.ask_assistant": "Saba AI Assistant gusobanura ibi bimenyetso",
        "decisions.field_signal": "Amakuru aheruka y'abahinzi (iminsi 30 ishize)",
        "decisions.field_signal_note": "Aya ni amakuru yatanzwe n'abahinzi yo kumenya ibiri kuba; si inama zemejwe cyangwa imibare ya NISR. Ntabwo ahindura impuzandengo y'umusaruro yo mu bihe byashize.",
        "decisions.field_signal_empty": "Nta makuru y'abahinzi yatanzwe muri aka gace mu minsi 30 ishize.",
        "decisions.field_signal_metric": "Ikimenyetso cyatangajwe mu murima",
        "decisions.field_signal_count": "amakuru {count}",
        "decisions.field_signal_unavailable": "Amakuru yo mu murima ntaraboneka ubu.",
        "plan.page_title": "Igenamigambi",
        "plan.header": "Igenamigambi ry'Igihembwe",
        "plan.subtitle": "Ingengabihe n'ishyirwa mu bikorwa by'ibikorwa by'ubuhinzi.",
        "plan.context_header": "Imiterere y'Igenamigambi",
        "plan.select_zone": "Hitamo Agace",
        "plan.season": "Igihembwe cy'Ihinga",
        "plan.season_a": "Igihembwe A",
        "plan.season_b": "Igihembwe B",
        "plan.season_c": "Igihembwe C",
        "plan.zone_all": "Intara Zose",
        "plan.zone_north": "Intara y'Amajyaruguru",
        "plan.zone_east": "Intara y'Iburasirazuba",
        "plan.zone_south": "Intara y'Amajyepfo",
        "plan.zone_west": "Intara y'Iburengerazuba",
        "plan.roadmap_title": "Ingengabihe y'Ibikorwa: {zone} ({season})",
        "plan.empty": "Nta makuru y'igenamigambi aboneka kuri ibi byatoranijwe.",
        "plan.chart_title": "Gahunda y'Ibikorwa",
        "plan.detailed_steps": "Intambwe Zose mu Burambuye",
        "plan.due": "Izarangira",
        "plan.save_btn": "Bika & Sangiza Igenamigambi",
        "plan.phase.preparation": "Imyiteguro",
        "plan.phase.execution": "Gushyira mu Bikorwa",
        "plan.phase.monitoring": "Gukurikirana",
        "plan.task.seeds": "Gutumiza Imbuto",
        "plan.task.fertilizer": "Gukwirakwiza Ifumbire",
        "plan.task.training": "Amahugurwa yo Gutera",
        "plan.task.monitoring": "Gukurikirana Imihindagurikire",
        "seg.page_title": "Iteganyazoni",
        "seg.header": "Gusesengura ibyiciro by'ubuhinzi",
        "seg.subtitle": "Gereranya umusaruro wagaragajwe mu turere no mu bihembwe by'ubuhinzi mu Rwanda.",
        "seg.filters": "Akayunguruzo",
        "seg.season": "Igihembwe",
        "seg.crops": "Ibihingwa",
        "seg.priority_level": "Urwego rw'Uburemere",
        "seg.empty": "Nta makuru ahari. Nyamuneka reba niba seriveri ikora neza.",
        "seg.map_title": "Ikarita y'Uduce tw'Ibanze",
        "seg.yield_title": "Isesengura ry'Umusaruro",
        "seg.chart_title": "Umusaruro uteganyijwe ku Karere n'Urwego",
        "seg.axis_district": "Akarere",
        "seg.axis_yield": "Umusaruro uteganyijwe (MT)",
        "seg.summary_title": "Incamake y'Iteganyazoni",
        "seg.col_district": "Akarere",
        "seg.col_crop": "Igihingwa",
        "seg.col_priority": "Uburemere",
        "seg.col_yield": "Umusaruro uteganyijwe (MT)",
        "comm.page_title": "Itumanaho",
        "comm.header": "Itumanaho Ryihuse",
        "comm.subtitle": "Integuza z'ako kanya, amakuru mashya, no guhuza ibikorwa by'abafatanyabikorwa.",
        "comm.feed_title": "Urutonde rw'Integuza",
        "comm.feed_empty": "Nta nteguza nshya zihari cyangwa seriveri ntiri kuboneka.",
        "comm.share_title": "Sangiza Amakuru",
        "comm.target_audience": "Abo Bigenewe",
        "comm.audience.extension": "Abashinzwe Ubuhinzi",
        "comm.audience.coop": "Abayobozi b'Amakoperative",
        "comm.audience.planners": "Abategura Igenamigambi",
        "comm.audience.all": "Abafatanyabikorwa Bose",
        "comm.message_label": "Ubutumwa / Itangazo",
        "comm.is_urgent": "Shyiraho ko Byihutirwa",
        "comm.send_btn": "Ohereza Ubutumwa",
        "comm.success": "Ubutumwa bwoherejwe kuri: {group}!",
        "comm.error_empty": "Nyamuneka andika ubutumwa mbere yo kohereza.",
        "comm.alert_type.warning": "Iburira",
        "comm.alert_type.info": "Amakuru",
        "comm.alert_type.urgent": "Byihutirwa",
        "error.404.title": "Paji Ntibonetse",
        "error.404.desc": "Paji mwashakaga ntibaho cyangwa yimuwe.",
        "error.network.title": "Ikibazo cy'Urusobe",
        "error.network.desc": "Guhuza na seriveri byanze. Nyamuneka reba interineti yawe wongere ugerageze.",
        "error.validation.title": "Ikibazo cy'Amakuru",
        "error.validation.desc": "Amakuru mwataye ntabwo ariyo. Nyamuneka suzuma ibyo mwanditse.",
        "error.system.title": "Ikibazo cya Sisitemu",
        "error.system.desc": "Habaye ikibazo gitunguranye muri sisitemu. Ikipe yacu yabimenyeshejwe.",
        "error.go_home": "Subira Ahabanza",
    },
    "fr": {
        "common.language": "Langue",
        "common.all_regions": "Toutes les Régions",
        "common.crop": "Culture",
        "common.district": "District",
        "common.status": "Statut",
        "common.pending": "En attente",
        "common.unknown_area": "Zone Inconnue",
        "common.unknown_crop": "Culture Inconnue",
        "common.unknown_task": "Tâche Inconnue",
        "common.built_for": "Développé pour le Hackathon Big Data NISR 2026",
        "priority.high": "Élevée",
        "priority.medium": "Moyenne",
        "priority.low": "Faible",
        "home.app_title": "agrimenya",
        "home.subtitle": "Système d'Aide à la Décision et à la Planification pour la Productivité Agricole",
        "home.welcome": "Bienvenue sur **agrimenya**. Cette plateforme permet aux planificateurs, agents de vulgarisation et dirigeants de coopératives de prendre des décisions éclairées grâce aux données SAS, AHS et EICV7.",
        "home.kpi.farmers": "Total des Agriculteurs Soutenus",
        "home.kpi.yield": "Augmentation Moyenne du Rendement",
        "home.kpi.cooperatives": "Coopératives Actives",
        "home.pillars_title": "Piliers Fondamentaux",
        "pillar.segmentation.title": "Segmenter",
        "pillar.segmentation.desc": "Identifier les zones prioritaires selon les rendements et les risques.",
        "pillar.segmentation.btn": "Segmenter",
        "pillar.decisions.title": "Décider",
        "pillar.decisions.desc": "Consulter les priorités, leurs éléments de preuve et les actions prévues.",
        "pillar.decisions.btn": "Décider",
        "pillar.planification.title": "Planifier",
        "pillar.planification.desc": "Planifier et suivre les feuilles de route et l'exécution agricole.",
        "pillar.planification.btn": "Planifier",
        "pillar.communication.title": "Communiquer",
        "pillar.communication.desc": "Diffuser des alertes, des plans et coordonner les parties prenantes.",
        "pillar.communication.btn": "Communiquer",
        "decisions.page_title": "Prise de Décision",
        "decisions.header": "Prise de Décision",
        "decisions.subtitle": "Données agricoles locales pour planifier et assurer le suivi.",
        "decisions.empty": "Aucune recommandation disponible actuellement ou le backend est inaccessible.",
        "decisions.act_btn": "Agir",
        "decisions.role_note": "Cette page présente des évaluations structurées à partir des données disponibles. Pour poser des questions et obtenir des explications, utilisez AI Assistant.",
        "decisions.priority_item": "Priorité {number}",
        "decisions.no_detail": "Aucun détail justificatif n'est disponible pour cet élément.",
        "decisions.evidence_title": "Éléments à prendre en compte",
        "decisions.evidence_note": "Consultez les observations récentes en complément des priorités. Les signalements communautaires ne sont ni des statistiques vérifiées ni des conseils validés.",
        "decisions.zone_context": "Sélectionner une zone",
        "decisions.zone_required": "Ajoutez ou chargez une zone pour consulter ses observations récentes.",
        "decisions.ask_assistant": "Demander à AI Assistant d'expliquer ces éléments",
        "decisions.field_signal": "Observations récentes des agriculteurs (30 derniers jours)",
        "decisions.field_signal_note": "Ces observations donnent un signal de terrain, pas un conseil vérifié ni des données officielles du NISR. Elles ne modifient pas la référence historique de rendement.",
        "decisions.field_signal_empty": "Aucune observation d'agriculteur dans cette zone au cours des 30 derniers jours.",
        "decisions.field_signal_metric": "Signal de terrain déclaré",
        "decisions.field_signal_count": "{count} observations",
        "decisions.field_signal_unavailable": "Les observations de terrain sont temporairement indisponibles.",
        "plan.page_title": "Planification",
        "plan.header": "Planification Agricole",
        "plan.subtitle": "Feuilles de route et calendriers d'exécution des interventions agricoles.",
        "plan.context_header": "Contexte du Plan",
        "plan.select_zone": "Sélectionner la Zone",
        "plan.season": "Saison",
        "plan.season_a": "Saison A",
        "plan.season_b": "Saison B",
        "plan.season_c": "Saison C",
        "plan.zone_all": "Toutes les Régions",
        "plan.zone_north": "Province du Nord",
        "plan.zone_east": "Province de l'Est",
        "plan.zone_south": "Province du Sud",
        "plan.zone_west": "Province de l'Ouest",
        "plan.roadmap_title": "Feuille de Route d'Exécution : {zone} ({season})",
        "plan.empty": "Aucune donnée de feuille de route disponible pour les critères sélectionnés.",
        "plan.chart_title": "Calendrier des Interventions",
        "plan.detailed_steps": "Étapes Détaillées",
        "plan.due": "Échéance",
        "plan.save_btn": "Enregistrer & Partager le Plan",
        "plan.phase.preparation": "Préparation",
        "plan.phase.execution": "Exécution",
        "plan.phase.monitoring": "Suivi & Évaluation",
        "plan.task.seeds": "Approvisionnement en Semences",
        "plan.task.fertilizer": "Distribution d'Engrais",
        "plan.task.training": "Formation aux Semis",
        "plan.task.monitoring": "Suivi des Cultures",
        "seg.page_title": "Segmentation",
        "seg.header": "Segmentation agricole",
        "seg.subtitle": "Comparez les productions agricoles observées par district et par saison au Rwanda.",
        "seg.filters": "Filtres",
        "seg.season": "Saison",
        "seg.crops": "Cultures",
        "seg.priority_level": "Niveau de Priorité",
        "seg.empty": "Aucune donnée disponible. Veuillez vérifier la connexion au backend.",
        "seg.map_title": "Carte des Zones Prioritaires",
        "seg.yield_title": "Analyse des Rendements",
        "seg.chart_title": "Production Estimée par District et Priorité",
        "seg.axis_district": "District",
        "seg.axis_yield": "Production Estimée (MT)",
        "seg.summary_title": "Résumé du Zonage",
        "seg.col_district": "District",
        "seg.col_crop": "Culture",
        "seg.col_priority": "Priorité",
        "seg.col_yield": "Production Estimée (MT)",
        "comm.page_title": "Communication",
        "comm.header": "Communication Efficace",
        "comm.subtitle": "Alertes en temps réel, mises à jour et coordination entre les acteurs.",
        "comm.feed_title": "Flux d'Alertes",
        "comm.feed_empty": "Aucune nouvelle alerte ou serveur inaccessible.",
        "comm.share_title": "Partager des Informations",
        "comm.target_audience": "Public Cible",
        "comm.audience.extension": "Agents de Vulgarisation",
        "comm.audience.coop": "Dirigeants de Coopératives",
        "comm.audience.planners": "Planificateurs Publics",
        "comm.audience.all": "Toutes les Parties Prenantes",
        "comm.message_label": "Message / Annonce",
        "comm.is_urgent": "Marquer comme Urgent",
        "comm.send_btn": "Envoyer la Mise à Jour",
        "comm.success": "Message envoyé à : {group} !",
        "comm.error_empty": "Veuillez saisir un message avant l'envoi.",
        "comm.alert_type.warning": "Avertissement",
        "comm.alert_type.info": "Information",
        "comm.alert_type.urgent": "Urgent",
        "error.404.title": "Page Non Trouvée",
        "error.404.desc": "La page que vous recherchez n'existe pas ou a été déplacée.",
        "error.network.title": "Erreur Réseau",
        "error.network.desc": "Échec de connexion au serveur. Veuillez vérifier votre connexion et réessayer.",
        "error.validation.title": "Erreur de Validation",
        "error.validation.desc": "Les données fournies sont invalides. Veuillez vérifier vos saisies.",
        "error.system.title": "Erreur Système",
        "error.system.desc": "Une erreur système inattendue s'est produite. Notre équipe en a été informée.",
        "error.go_home": "Retour à l'Accueil",
    }
}


class LocalizationManager:
    """
    Robust Localization Manager to handle GNU gettext with a safe fallback mechanism.
    Tracks active locale via Streamlit's session_state.
    """
    def __init__(self, domain: str = "messages", locale_dir: str = "locales"):
        self.domain = domain
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.locale_dir = os.path.join(self.base_dir, locale_dir)
        self._translators: Dict[str, gettext.GNUTranslations] = {}
        
    def _get_active_lang(self) -> str:
        if "language" not in st.session_state:
            st.session_state["language"] = DEFAULT_LANGUAGE
        return st.session_state["language"]

    def set_language(self, lang_code: str) -> None:
        if lang_code in LANGUAGES:
            st.session_state["language"] = lang_code

    def _load_gettext(self, lang: str) -> Optional[gettext.GNUTranslations]:
        if lang in self._translators:
            return self._translators[lang]
        
        try:
            translator = gettext.translation(
                domain=self.domain,
                localedir=self.locale_dir,
                languages=[lang],
            )
            self._translators[lang] = translator
            return translator
        except FileNotFoundError:
            # Expected if .mo files are not compiled yet, will use custom fallback
            return None
        except Exception as e:
            logger.warning("Error loading gettext for lang %s: %s", lang, e)
            return None

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """Translates a given key using GNU gettext, falling back to the dictionary."""
        lang = self._get_active_lang()
        translator = self._load_gettext(lang)
        
        translated = None
        
        # 1. Try GNU gettext
        if translator:
            # gettext returns the original key if translation is not found
            candidate = translator.gettext(key)
            if candidate != key:
                translated = candidate
                
        # 2. Try Fallback dictionary
        if translated is None:
            translated = FALLBACK_TRANSLATIONS.get(lang, {}).get(key)
            
        # 3. Fallback to English dictionary
        if translated is None and lang != DEFAULT_LANGUAGE:
            translated = FALLBACK_TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key)
            
        # 4. Final fallback
        if translated is None:
            translated = default if default is not None else key
            
        # Format kwargs if any
        if kwargs:
            try:
                return translated.format(**kwargs)
            except Exception:
                return translated
        return translated


# Initialize global manager
_l10n_manager = LocalizationManager()

def get_current_language() -> str:
    """Return active language code."""
    return _l10n_manager._get_active_lang()

def set_language(lang_code: str) -> None:
    """Set active language code."""
    _l10n_manager.set_language(lang_code)

def t(key: str, default: str = None, **kwargs) -> str:
    """Alias for standard translation method."""
    return _l10n_manager.translate(key, default, **kwargs)

def render_language_selector(sidebar: bool = True) -> None:
    """Render an explicit, accessible English/Kinyarwanda language control."""
    current_code = get_current_language()
    target = st.sidebar if sidebar else st.container()
    with target:
        options = ["en", "rw"]
        if current_code not in options:
            current_code = DEFAULT_LANGUAGE
        st.selectbox(
            "Language / Ururimi",
            options=options,
            index=options.index(current_code),
            format_func=lambda code: "English · EN" if code == "en" else "Ikinyarwanda · RW",
            key="global_language_selector",
            on_change=lambda: set_language(st.session_state["global_language_selector"]),
            label_visibility="collapsed",
            width="stretch",
        )
