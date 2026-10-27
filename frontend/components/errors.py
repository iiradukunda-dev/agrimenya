"""
Error page component - renders executive Liquid Glass error states for all error types.
Provides render_error_page() and error_boundary() context manager.
"""
import logging
import os
import re
from contextlib import ContextDecorator
from html import escape
from typing import Any

import requests
import streamlit as st
from utils.i18n import t

logger = logging.getLogger(__name__)


def _sanitize_details(details: str) -> str:
    """Sanitize technical details to prevent sensitive data leaks."""
    if not details:
        return ""
    text = str(details)
    # Mask Bearer tokens, JWTs, and API keys
    text = re.sub(r'Bearer\s+[A-Za-z0-9\-_.]+', 'Bearer [REDACTED_TOKEN]', text)
    text = re.sub(r'ey[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*', '[REDACTED_JWT]', text)
    text = re.sub(r'((?:password|secret|key|token|auth)=)[^&\s]+', r'\1[REDACTED]', text, flags=re.IGNORECASE)
    # Mask Database URIs (e.g. postgresql://user:pass@host/db)
    text = re.sub(r'(?:postgres|postgresql|mysql|sqlite)://[^\s@]+@', r'postgresql://[REDACTED_DB_CREDENTIALS]@', text)
    return text[:2000]


def _get_error_config(error_type: str, details: str | None = None) -> dict[str, Any]:
    """Return styling tokens, badge, and SVG icon for the given error type.
    
    Automatically refines generic network/system errors if details contain specific HTTP codes.
    """
    norm = error_type.lower().strip()

    # Intelligent auto-refinement if details contain recognizable HTTP status codes
    if norm in ("network", "system", "default") and details:
        det_lower = details.lower()
        if "401" in det_lower or "unauthorized" in det_lower:
            norm = "unauthorized"
        elif "403" in det_lower or "forbidden" in det_lower:
            norm = "forbidden"
        elif "404" in det_lower or "not found" in det_lower:
            norm = "404"
        elif "422" in det_lower or "validation" in det_lower:
            norm = "validation"
        elif "503" in det_lower or "service unavailable" in det_lower or "502" in det_lower:
            norm = "database"
        elif "504" in det_lower or "timeout" in det_lower or "timed out" in det_lower:
            norm = "timeout"
    
    # 404 / Not Found
    if norm in ("404", "not_found"):
        return {
            "key": "404",
            "badge": "404 • NOT FOUND",
            "accent": "#38bdf8",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
            </svg>"""
        }
    
    # 401 / Unauthorized
    if norm in ("401", "unauthorized", "auth"):
        return {
            "key": "unauthorized",
            "badge": "401 • AUTHENTICATION REQUIRED",
            "accent": "#0284c7",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>"""
        }
        
    # 403 / Forbidden
    if norm in ("403", "forbidden"):
        return {
            "key": "forbidden",
            "badge": "403 • ACCESS RESTRICTED",
            "accent": "#f87171",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <line x1="4.5" y1="9" x2="19.5" y2="15"/>
            </svg>"""
        }
        
    # Timeout
    if norm in ("timeout", "gateway_timeout", "504"):
        return {
            "key": "timeout",
            "badge": "TIMEOUT • SERVICE DELAY",
            "accent": "#f59e0b",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
            </svg>"""
        }
        
    # Network / Connection
    if norm in ("network", "connection", "offline"):
        return {
            "key": "network",
            "badge": "OFFLINE • NETWORK FAILURE",
            "accent": "#f59e0b",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 1l22 22"/>
                <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
                <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
                <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
                <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
                <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
                <line x1="12" y1="20" x2="12.01" y2="20"/>
            </svg>"""
        }
        
    # Validation / 422
    if norm in ("validation", "422", "bad_request", "400"):
        return {
            "key": "validation",
            "badge": "422 • VALIDATION ERROR",
            "accent": "#f59e0b",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>"""
        }
        
    # Database / 503
    if norm in ("database", "503", "502", "unavailable", "service_unavailable"):
        return {
            "key": "database",
            "badge": "503 • SERVICE UNAVAILABLE",
            "accent": "#0ea5e9",
            "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#0ea5e9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
            </svg>"""
        }
        
    # System / 500 default
    return {
        "key": "system",
        "badge": "500 • SYSTEM ERROR",
        "accent": "#38bdf8",
        "icon": """<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
            <rect x="9" y="9" width="6" height="6"/>
            <line x1="9" y1="1" x2="9" y2="4"/>
            <line x1="15" y1="1" x2="15" y2="4"/>
            <line x1="9" y1="20" x2="9" y2="23"/>
            <line x1="15" y1="20" x2="15" y2="23"/>
            <line x1="20" y1="9" x2="23" y2="9"/>
            <line x1="20" y1="14" x2="23" y2="14"/>
            <line x1="1" y1="9" x2="4" y2="9"/>
            <line x1="1" y1="14" x2="4" y2="14"/>
        </svg>"""
    }


def render_error_page(
    error_type: str = "system",
    details: str | None = None,
    custom_title: str | None = None,
    custom_desc: str | None = None,
    show_retry: bool = True,
    show_contact: bool = True,
) -> None:
    """Renders a modern, executive Liquid Glass error page with contextual messaging and actions.

    Args:
        error_type: Error category ('404', 'network', 'timeout', 'unauthorized', 'forbidden', 'validation', 'database', 'system').
        details: Optional technical detail string (sanitized and shown in expander).
        custom_title: Optional override for the error heading.
        custom_desc: Optional override for the error explanation.
        show_retry: Whether to show a 'Try Again' action button.
        show_contact: Whether to show a 'Report an Issue' action button.
    """
    cfg = _get_error_config(error_type, details)
    err_key = cfg["key"]
    accent = cfg["accent"]
    badge = cfg["badge"]
    icon_svg = cfg["icon"]

    title = custom_title or t(f"error.{err_key}.title", f"{err_key.title()} Error")
    desc = custom_desc or t(
        f"error.{err_key}.desc",
        "An unexpected issue occurred while processing your request. Please try again or return home."
    )

    card_html = f"""
    <div style="
        background: linear-gradient(135deg, rgba(8, 26, 38, 0.94) 0%, rgba(5, 18, 27, 0.98) 100%);
        border: 1px solid rgba(56, 189, 248, 0.28);
        border-top: 2px solid {accent};
        border-radius: 20px;
        padding: 2.2rem 1.8rem 1.8rem;
        text-align: center;
        box-shadow: 0 20px 48px rgba(0, 0, 0, 0.5), 0 0 20px {accent}22;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        margin: 1.5rem auto 1.2rem;
        max-width: 560px;
    ">
        <div style="
            width: 68px;
            height: 68px;
            margin: 0 auto 1.15rem;
            border-radius: 50%;
            background: radial-gradient(circle, {accent}25 0%, rgba(3, 29, 40, 0.6) 100%);
            border: 1.5px solid {accent}55;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 24px {accent}35;
        ">
            {icon_svg}
        </div>
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            background: {accent}18;
            border: 1px solid {accent}45;
            color: {accent};
            font-size: 0.72rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        ">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: {accent}; box-shadow: 0 0 8px {accent};"></span>
            {badge}
        </div>
        <h2 style="
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
            margin: 0 0 0.6rem;
            letter-spacing: -0.02em;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
        ">{escape(title)}</h2>
        <p style="
            color: #cbe5f5;
            font-size: 0.92rem;
            line-height: 1.6;
            margin: 0 0 0.8rem;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
        ">{escape(desc)}</p>
    </div>
    """

    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        st.markdown(card_html, unsafe_allow_html=True)

        # Sanitized technical details popover
        sanitized = _sanitize_details(details) if details else ""
        if sanitized:
            with st.popover("Technical Diagnostic Information", use_container_width=True):
                st.code(sanitized, language="text")

        # Contextual Action Buttons
        btn_count = 1 + (1 if show_retry else 0) + (1 if show_contact else 0)
        btn_cols = st.columns(btn_count)
        c_idx = 0

        # Primary Action
        with btn_cols[c_idx]:
            c_idx += 1
            if err_key == "unauthorized":
                if st.button(t("error.signin", "Sign In"), type="primary", use_container_width=True, key=f"btn_err_signin_{err_key}"):
                    st.switch_page("pages/10_Admin.py")
            else:
                if st.button(t("error.go_home", "Return to Home"), type="primary", use_container_width=True, key=f"btn_err_home_{err_key}"):
                    st.switch_page("Home.py")

        # Retry Action
        if show_retry:
            with btn_cols[c_idx]:
                c_idx += 1
                if st.button(t("error.retry", "Try Again"), use_container_width=True, key=f"btn_err_retry_{err_key}"):
                    st.rerun()

        # Contact Action
        if show_contact:
            with btn_cols[c_idx]:
                c_idx += 1
                if st.button(t("error.contact", "Report Issue"), use_container_width=True, key=f"btn_err_contact_{err_key}"):
                    st.switch_page("pages/11_Contact.py")


class error_boundary(ContextDecorator):
    """Gracefully catch all runtime, network, HTTP, and schema exceptions in a view and render a tailored error page.
    
    Can be used as a context manager:
        with error_boundary("Dashboard"):
            render_dashboard()
            
    Or as a decorator:
        @error_boundary("Dashboard")
        def render_dashboard():
            ...
    """

    def __init__(self, view_name: str = "Workspace View"):
        self.view_name = view_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            return False

        # Never intercept Streamlit internal flow control (StopException, RerunException)
        if isinstance(exc_val, BaseException) and not isinstance(exc_val, Exception):
            return False

        details = str(exc_val)

        # Connection errors
        if isinstance(exc_val, (requests.exceptions.ConnectionError, ConnectionError, ConnectionRefusedError, ConnectionResetError)):
            logger.error("Connection error in %s: %s", self.view_name, exc_val)
            render_error_page("network", details=details)
            return True

        # Timeout errors
        if isinstance(exc_val, (requests.exceptions.Timeout, TimeoutError)):
            logger.error("Timeout error in %s: %s", self.view_name, exc_val)
            render_error_page("timeout", details=details)
            return True

        # HTTP / Request exceptions with status codes
        if isinstance(exc_val, (requests.exceptions.HTTPError, requests.exceptions.RequestException)):
            logger.error("Request error in %s: %s", self.view_name, exc_val)
            resp = getattr(exc_val, "response", None)
            status_code = getattr(resp, "status_code", None)
            if status_code == 404:
                render_error_page("404", details=details)
            elif status_code == 401:
                render_error_page("unauthorized", details=details)
            elif status_code == 403:
                render_error_page("forbidden", details=details)
            elif status_code == 422:
                render_error_page("validation", details=details)
            elif status_code in (502, 503):
                render_error_page("database", details=details)
            elif status_code == 504:
                render_error_page("timeout", details=details)
            elif status_code is not None and status_code >= 500:
                render_error_page("system", details=details)
            else:
                render_error_page("network", details=details)
            return True

        # Permission errors
        if isinstance(exc_val, PermissionError):
            logger.warning("Permission error in %s: %s", self.view_name, exc_val)
            render_error_page("forbidden", details=details)
            return True

        # Not found errors
        if isinstance(exc_val, FileNotFoundError):
            logger.warning("File not found in %s: %s", self.view_name, exc_val)
            render_error_page("404", details=details)
            return True

        # Validation errors
        if isinstance(exc_val, ValueError):
            logger.warning("Validation error in %s: %s", self.view_name, exc_val)
            render_error_page("validation", details=details)
            return True

        # All other unhandled exceptions
        logger.exception("Unhandled error in %s: %s", self.view_name, exc_val)
        render_error_page("system", details=details)
        return True

