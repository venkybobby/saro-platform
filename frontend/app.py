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

from frontend.tabs import dashboard as dashboard_tab
from frontend.tabs import reports as reports_tab
from frontend.tabs import upload as upload_tab
from frontend.tabs import remedy as remedy_tab

_API_BASE = os.environ.get("SARO_API_URL", "http://localhost:8000").rstrip("/")
_API_IS_LOCALHOST = "localhost" in _API_BASE or "127.0.0.1" in _API_BASE


def _check_bootstrap() -> dict | None:
    """
    Call GET /health and return JSON if reachable, else None.

    Result is cached in session_state for 30 seconds to avoid a remote HTTP
    round-trip on every Streamlit re-render (every button click triggers a
    full script re-run, so without caching the login page makes a /health
    request on each interaction — the main cause of Issue 1 login slowness).
    """
    import time
    cache_key = "_health_cache"
    ts_key = "_health_cache_ts"
    now = time.monotonic()
    cached_ts = st.session_state.get(ts_key, 0)
    if now - cached_ts < 30 and cache_key in st.session_state:
        return st.session_state[cache_key]
    try:
        r = requests.get(f"{_API_BASE}/health", timeout=10)
        if r.status_code == 200:
            result = r.json()
            st.session_state[cache_key] = result
            st.session_state[ts_key] = now
            return result
    except Exception:
        pass
    # Cache the failure too so we don't hammer a cold-starting backend
    st.session_state[cache_key] = None
    st.session_state[ts_key] = now
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


def _do_demo_signup(
    first_name: str,
    last_name: str,
    email: str,
    contact_number: str,
    company_name: str,
    message: str,
) -> bool:
    """Call POST /api/v1/demo/signup; return True on success."""
    try:
        resp = requests.post(
            f"{_API_BASE}/api/v1/demo/signup",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "contact_number": contact_number or None,
                "company_name": company_name or None,
                "message": message or None,
            },
            timeout=20,
        )
        if resp.status_code in (200, 201):
            return True
        detail = resp.json().get("detail", resp.text)
        st.error(f"Signup failed ({resp.status_code}): {detail}")
        return False
    except requests.ConnectionError:
        st.error(f"❌ Cannot reach the API at `{_API_BASE}`.")
        return False
    except Exception as exc:
        st.error(f"Signup error: {exc}")
        return False


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="SARO — Smart AI Risk Orchestrator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "SARO — Smart AI Risk Orchestrator v1.0"},
)

# ── Session state defaults ────────────────────────────────────────────────────

for key, default in [("token", None), ("user", None), ("last_report", None), ("demo_submitted", False)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Login helpers ─────────────────────────────────────────────────────────────


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
                f"- `SARO_API_URL` is **`{_API_BASE}`** — verify this is the backend URL.\n"
                f"- The backend may still be starting — wait ~30 s and retry.\n"
                f"- Check Koyeb logs for the **saro-api** service."
            )
        else:
            st.error(f"Login failed ({code}): {e}")
        return False
    except requests.ConnectionError:
        st.error(
            f"❌ Cannot connect to the SARO API at **`{_API_BASE}`**.\n\n"
            + (
                "Set `SARO_API_URL` in Koyeb **saro-frontend** → **Environment variables**."
                if _API_IS_LOCALHOST
                else "Check that the backend service is running and reachable."
            )
        )
        return False
    except requests.Timeout:
        st.error(f"⏱ Request timed out. The backend may be cold-starting — wait 30 s and retry.")
        return False


def _render_login() -> None:
    st.title("🛡️ SARO — Smart AI Risk Orchestrator")

    if _API_IS_LOCALHOST:
        st.warning(
            "⚠️ **API not configured.** `SARO_API_URL` is not set — login will fail.\n\n"
            "| Key | Value |\n|---|---|\n"
            "| `SARO_API_URL` | `https://saro-api-<your-org>.koyeb.app` |",
            icon="⚠️",
        )

    health_data = _check_bootstrap()
    bootstrap_needed = health_data.get("bootstrap_needed") if health_data else None

    if bootstrap_needed is True:
        st.info("🚀 **First-run setup required.** No accounts exist yet.")
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
        return

    if bootstrap_needed is None and health_data is None:
        st.warning(f"⚠️ Cannot reach the API at `{_API_BASE}`. Refresh to retry.")

    # ── Login / Demo tabs ─────────────────────────────────────────────────────
    login_tab, demo_tab = st.tabs(["🔐 Sign In", "🚀 Request Demo"])

    with login_tab:
        st.subheader("Sign in to SARO")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="operator@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            if not email or not password:
                st.warning("Please enter email and password.")
            else:
                if _login(email, password):
                    st.rerun()

    with demo_tab:
        _render_demo_signup()


def _render_demo_signup() -> None:
    """Render the public demo/trial signup form."""
    st.subheader("Request a Demo")
    st.write(
        "Interested in SARO for your organisation? Fill in your details and "
        "our team will be in touch to schedule a personalised demo."
    )

    if st.session_state.get("demo_submitted"):
        st.success(
            "✅ **Thank you for your interest!**  \n"
            "We've received your request and will be in touch within 1–2 business days."
        )
        if st.button("Submit another request"):
            st.session_state["demo_submitted"] = False
            st.rerun()
        return

    with st.form("demo_signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First name *", placeholder="Jane")
        with col2:
            last_name = st.text_input("Last name *", placeholder="Smith")

        email = st.text_input("Work email *", placeholder="jane.smith@company.com")
        company_name = st.text_input("Company name", placeholder="Acme Corp")
        contact_number = st.text_input("Contact number", placeholder="+44 7700 900000")
        message = st.text_area(
            "Tell us about your use case",
            placeholder="We're looking to audit our NLP model for bias and compliance...",
            height=100,
        )
        submitted = st.form_submit_button("🚀 Request Demo", use_container_width=True, type="primary")

    if submitted:
        if not first_name or not last_name or not email:
            st.warning("First name, last name and email are required.")
        else:
            if _do_demo_signup(first_name, last_name, email, contact_number, company_name, message):
                st.session_state["demo_submitted"] = True
                st.rerun()


# ── Authenticated layout ───────────────────────────────────────────────────────


def _render_app() -> None:
    user = st.session_state["user"]
    token: str = st.session_state["token"]

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

        # Use cached health data (refreshed every 30 s) — avoids an extra
        # round-trip to Koyeb on every sidebar render (Issue 1 fix).
        health = _check_bootstrap() or {}
        db_status = health.get("database", "unknown")
        colour = "green" if db_status == "ok" else "red"
        api_colour = "green" if health else "red"
        st.markdown(f"**API:** :{api_colour}[{'online' if health else 'offline'}]  **DB:** :{colour}[{db_status}]")

        st.divider()
        if st.button("Sign out", use_container_width=True):
            st.session_state["token"] = None
            st.session_state["user"] = None
            st.rerun()

    # Main tabs — Dashboard visible to all roles; Demo Requests only for super_admin
    if user.get("role") == "super_admin":
        tab_dashboard, tab_upload, tab_reports, tab_remedy, tab_demo_requests = st.tabs(
            ["🏠 Dashboard", "📤 Upload & Scan", "📊 Reports", "🔧 Remedy", "📋 Demo Requests"]
        )
        with tab_demo_requests:
            _render_demo_requests(token)
    else:
        tab_dashboard, tab_upload, tab_reports, tab_remedy = st.tabs(
            ["🏠 Dashboard", "📤 Upload & Scan", "📊 Reports", "🔧 Remedy"]
        )

    with tab_dashboard:
        dashboard_tab.render(token)

    with tab_upload:
        upload_tab.render(token)

    with tab_reports:
        reports_tab.render(token)

    with tab_remedy:
        remedy_tab.render(token)


def _render_demo_requests(token: str) -> None:
    """Super-admin view: list and manage demo requests."""
    st.header("📋 Demo Requests")

    status_filter = st.selectbox(
        "Filter by status",
        ["All", "pending", "contacted", "converted", "rejected"],
        key="demo_status_filter",
    )

    try:
        param = "" if status_filter == "All" else f"?status={status_filter}"
        resp = requests.get(
            f"{_API_BASE}/api/v1/demo/requests{param}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=20,
        )
        resp.raise_for_status()
        requests_data: list[dict] = resp.json()
    except Exception as e:
        st.error(f"Failed to load demo requests: {e}")
        return

    if not requests_data:
        st.info("No demo requests found.")
        return

    st.metric("Total requests", len(requests_data))

    for req in requests_data:
        status_badge = {
            "pending": "🟡 Pending",
            "contacted": "🟢 Contacted",
            "converted": "✅ Converted",
            "rejected": "🔴 Rejected",
        }.get(req["status"], req["status"])

        with st.expander(
            f"**{req['first_name']} {req['last_name']}** — {req['email']} — {status_badge}",
            expanded=req["status"] == "pending",
        ):
            c1, c2 = st.columns(2)
            c1.write(f"**Company:** {req.get('company_name') or '—'}")
            c2.write(f"**Phone:** {req.get('contact_number') or '—'}")
            c1.write(f"**Submitted:** {req['created_at'][:19]}")
            c2.write(f"**Status:** {req['status']}")
            if req.get("message"):
                st.write("**Message:**")
                st.write(req["message"])

            # Status update
            new_status = st.selectbox(
                "Update status",
                ["pending", "contacted", "converted", "rejected"],
                index=["pending", "contacted", "converted", "rejected"].index(req["status"]),
                key=f"demo_status_{req['id']}",
            )
            if st.button("Update", key=f"demo_update_{req['id']}"):
                try:
                    patch_resp = requests.patch(
                        f"{_API_BASE}/api/v1/demo/requests/{req['id']}",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"status": new_status},
                        timeout=15,
                    )
                    patch_resp.raise_for_status()
                    st.success(f"Updated to **{new_status}**")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    if st.session_state["token"] is None:
        _render_login()
    else:
        _render_app()


main()
