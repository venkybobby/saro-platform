"""
SARO Streamlit Application
===========================
Smart AI Risk Orchestrator — Progressive Web App frontend.

Run:
    streamlit run frontend/app.py

Requires env vars:
    SARO_API_URL  (default: http://localhost:8000)
"""
from __future__ import annotations

import os

import requests
import streamlit as st

from frontend.tabs import reports as reports_tab
from frontend.tabs import upload as upload_tab

_API_BASE = os.environ.get("SARO_API_URL", "http://localhost:8000").rstrip("/")
_API_IS_LOCALHOST = "localhost" in _API_BASE or "127.0.0.1" in _API_BASE

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SARO — Smart AI Risk Orchestrator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "SARO — Smart AI Risk Orchestrator v1.0",
    },
)

# ── Session state defaults ────────────────────────────────────────────────────

if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "last_report" not in st.session_state:
    st.session_state["last_report"] = None


# ── Login form ────────────────────────────────────────────────────────────────


def _login(email: str, password: str) -> bool:
    """Attempt login; return True on success."""
    try:
        resp = requests.post(
            f"{_API_BASE}/api/v1/auth/token",
            json={"email": email, "password": password},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        st.session_state["token"] = data["access_token"]

        # Fetch user profile
        me_resp = requests.get(
            f"{_API_BASE}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=15,
        )
        me_resp.raise_for_status()
        st.session_state["user"] = me_resp.json()
        return True

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            st.error("Invalid email or password.")
        else:
            st.error(f"Login failed: {e}")
        return False
    except requests.ConnectionError:
        st.error(
            f"❌ Cannot connect to the SARO API at **`{_API_BASE}`**.\n\n"
            + (
                "The `SARO_API_URL` environment variable is not set (or is still pointing at "
                "`localhost`). Set it to your backend's Koyeb URL, e.g. "
                "`https://saro-api-<org>.koyeb.app`, in the Koyeb frontend service → "
                "**Environment variables** panel."
                if _API_IS_LOCALHOST
                else "Check that the backend service is running and reachable."
            )
        )
        return False
    except requests.Timeout:
        st.error(f"⏱ Request to `{_API_BASE}` timed out. The backend may be cold-starting — please try again.")
        return False


def _render_login() -> None:
    st.title("🛡️ SARO — Smart AI Risk Orchestrator")
    st.subheader("Sign in")

    # ── Misconfiguration banner ───────────────────────────────────────────────
    if _API_IS_LOCALHOST:
        st.warning(
            "⚠️ **API not configured.** `SARO_API_URL` is not set — login will fail.\n\n"
            "Go to your Koyeb **saro-frontend** service → **Environment variables** and add:\n\n"
            "| Key | Value |\n|---|---|\n"
            "| `SARO_API_URL` | `https://saro-api-<your-org>.koyeb.app` |",
            icon="⚠️",
        )

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="operator@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Please enter email and password.")
        else:
            _login(email, password)
            st.rerun()


# ── Authenticated layout ───────────────────────────────────────────────────────


def _render_app() -> None:
    user = st.session_state["user"]
    token: str = st.session_state["token"]

    # Sidebar
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Shield_icon.svg/240px-Shield_icon.svg.png",
            width=60,
        )
        st.markdown("## SARO")
        st.caption("Smart AI Risk Orchestrator")
        st.divider()
        st.markdown(f"**User:** {user['email']}")
        st.markdown(f"**Role:** `{user['role']}`")
        st.divider()

        # Health badge
        try:
            health = requests.get(f"{_API_BASE}/health", timeout=5).json()
            db_status = health.get("database", "unknown")
            colour = "green" if db_status == "ok" else "red"
            st.markdown(f"**API:** :green[online]  **DB:** :{colour}[{db_status}]")
        except Exception:
            st.markdown("**API:** :red[offline]")

        st.divider()

        if st.button("Sign out", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()

    # Main tabs
    tab_upload, tab_reports = st.tabs(["📤 Upload & Scan", "📊 Reports"])

    with tab_upload:
        upload_tab.render(token)

    with tab_reports:
        reports_tab.render(token)


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    if st.session_state["token"] is None:
        _render_login()
    else:
        _render_app()


main()
