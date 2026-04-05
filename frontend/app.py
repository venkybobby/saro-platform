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


def _check_bootstrap() -> dict | None:
    """
    Call GET /health and return the JSON if the API is reachable, else None.
    Used to detect whether bootstrap is still needed (no users in DB yet).
    """
    try:
        r = requests.get(f"{_API_BASE}/health", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _do_bootstrap(org_name: str, email: str, password: str) -> bool:
    """Call POST /api/v1/auth/bootstrap; return True on success."""
    try:
        resp = requests.post(
            f"{_API_BASE}/api/v1/auth/bootstrap",
            json={"org_name": org_name, "email": email, "password": password},
            timeout=20,
        )
        if resp.status_code == 201:
            st.success(
                f"✅ First-run setup complete! "
                f"Tenant and super-admin account created for **{email}**. "
                "You can now sign in below."
            )
            return True
        elif resp.status_code == 409:
            st.info("Setup already completed — please sign in with your existing account.")
            return True
        else:
            detail = resp.json().get("detail", resp.text)
            st.error(f"Bootstrap failed ({resp.status_code}): {detail}")
            return False
    except requests.ConnectionError:
        st.error(
            f"❌ Cannot reach the API at `{_API_BASE}`. "
            "Check that `SARO_API_URL` is set correctly in Koyeb."
        )
        return False
    except Exception as exc:
        st.error(f"Bootstrap error: {exc}")
        return False

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
        code = e.response.status_code if e.response is not None else 0
        if code == 401:
            st.error("❌ Invalid email or password. Check your credentials and try again.")
        elif code == 503:
            st.error(
                f"🔴 **Backend service unavailable (503).**\n\n"
                f"Possible causes:\n"
                f"- `SARO_API_URL` is set to **`{_API_BASE}`** — verify this is the "
                f"**backend** service URL (not the frontend).\n"
                f"- The backend service is still starting up — wait ~30 s and retry.\n"
                f"- The backend crashed — check Koyeb logs for the **saro-api** service."
            )
        else:
            st.error(f"Login failed ({code}): {e}")
        return False
    except requests.ConnectionError:
        st.error(
            f"❌ Cannot connect to the SARO API at **`{_API_BASE}`**.\n\n"
            + (
                "The `SARO_API_URL` environment variable is not set (or is still pointing at "
                "`localhost`). Set it to your backend's Koyeb URL, e.g. "
                "`https://saro-api-<org>.koyeb.app`, in the Koyeb **saro-frontend** service → "
                "**Environment variables** panel."
                if _API_IS_LOCALHOST
                else "Check that the backend service is running and reachable."
            )
        )
        return False
    except requests.Timeout:
        st.error(
            f"⏱ Request to `{_API_BASE}` timed out. "
            "The backend may be cold-starting — please wait 30 s and try again."
        )
        return False


def _render_login() -> None:
    st.title("🛡️ SARO — Smart AI Risk Orchestrator")

    # ── Misconfiguration banner ───────────────────────────────────────────────
    if _API_IS_LOCALHOST:
        st.warning(
            "⚠️ **API not configured.** `SARO_API_URL` is not set — login will fail.\n\n"
            "Go to your Koyeb **saro-frontend** service → **Environment variables** and add:\n\n"
            "| Key | Value |\n|---|---|\n"
            "| `SARO_API_URL` | `https://saro-api-<your-org>.koyeb.app` |",
            icon="⚠️",
        )

    # ── First-run bootstrap check ─────────────────────────────────────────────
    # Call /health to see if any users exist yet.  If not, show the setup form
    # instead of the login form to avoid a chicken-and-egg situation where the
    # user has no credentials to log in with.
    health_data = _check_bootstrap()
    bootstrap_needed = health_data.get("bootstrap_needed") if health_data else None

    if bootstrap_needed is True:
        st.info(
            "🚀 **First-run setup required.**  "
            "No accounts exist yet. Create your super-admin account below."
        )
        with st.form("bootstrap_form"):
            st.subheader("Create super-admin account")
            org_name = st.text_input("Organisation name", placeholder="My Company")
            email_bs = st.text_input("Admin email", placeholder="admin@example.com")
            pw_bs = st.text_input("Password (min 8 chars)", type="password")
            submitted_bs = st.form_submit_button("Create account & continue", use_container_width=True)

        if submitted_bs:
            if not org_name or not email_bs or not pw_bs:
                st.warning("All fields are required.")
            elif len(pw_bs) < 8:
                st.warning("Password must be at least 8 characters.")
            else:
                if _do_bootstrap(org_name, email_bs, pw_bs):
                    st.rerun()
        return  # don't render the login form at the same time

    if bootstrap_needed is None and health_data is None:
        st.warning(
            f"⚠️ Cannot reach the API at `{_API_BASE}`. "
            "The backend may be starting up — please wait and refresh."
        )

    # ── Normal login form ─────────────────────────────────────────────────────
    st.subheader("Sign in")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="operator@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not email or not password:
            st.warning("Please enter email and password.")
        else:
            # Only rerun on SUCCESS — rerunning on failure clears st.error()
            # before Streamlit gets a chance to render it.
            if _login(email, password):
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
