"""
Remedy Tab — SARO Streamlit frontend.

Shows all failed / warned / flagged / triggered trace records for a selected
audit, grouped by gate.  Operators can review each issue and mark it as
remediated with optional notes.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import requests
import streamlit as st

logger = logging.getLogger(__name__)
_API_BASE = os.environ.get("SARO_API_URL", "http://localhost:8000").rstrip("/")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _get(path: str, token: str) -> Any:
    resp = requests.get(f"{_API_BASE}{path}", headers=_headers(token), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, token: str, json: dict) -> Any:
    resp = requests.post(f"{_API_BASE}{path}", headers=_headers(token), json=json, timeout=30)
    resp.raise_for_status()
    return resp.json()


def render(token: str) -> None:
    """Render the Remedy tab."""
    st.header("🔧 Remedy — Audit Issue Tracker")
    st.caption(
        "Review failed, warned, flagged and triggered checks from each audit. "
        "Mark items as remediated once you have addressed them."
    )

    # ── Load completed audits ─────────────────────────────────────────────────
    try:
        audits: list[dict] = _get("/api/v1/audits?limit=100", token)
    except requests.ConnectionError:
        st.error(f"Cannot connect to SARO API at `{_API_BASE}`.")
        return
    except requests.HTTPError as e:
        st.error(f"Failed to load audits: {e}")
        return

    completed = [a for a in audits if a["status"] in ("completed", "failed")]
    if not completed:
        st.info("No audits found. Run an audit from the **Upload & Scan** tab first.")
        return

    # ── Audit selector ─────────────────────────────────────────────────────────
    audit_options: dict[str, dict] = {
        f"{a['dataset_name'] or 'unnamed'} — {a['created_at'][:19]} "
        f"[{a['status'].upper()}]": a
        for a in completed
    }
    selected_label = st.selectbox(
        "Select audit to remediate",
        list(audit_options.keys()),
        key="remedy_audit_select",
    )
    if not selected_label:
        return

    selected_audit = audit_options[selected_label]
    audit_id = selected_audit["id"]

    # ── Trace summary ─────────────────────────────────────────────────────────
    try:
        summary: dict = _get(f"/api/v1/traces/{audit_id}/summary", token)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            st.info("No trace data available for this audit. Traces are only stored for audits run after the tracing update.")
        else:
            st.error(f"Failed to load trace summary: {e}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Checks", summary.get("total_traces", 0))
    col2.metric("Issues Found", summary.get("total_failed", 0))
    col3.metric("Remediated", summary.get("total_remediated", 0))
    pending = summary.get("pending_remediation", 0)
    col4.metric(
        "Pending",
        pending,
        delta=f"-{pending}" if pending == 0 else None,
        delta_color="normal",
    )

    if pending == 0 and summary.get("total_failed", 0) > 0:
        st.success("✅ All issues for this audit have been marked as remediated!")
    elif summary.get("total_failed", 0) == 0:
        st.success("✅ No issues detected in this audit — all checks passed.")
        return

    st.divider()

    # ── Toggle: show remediated items ─────────────────────────────────────────
    show_remediated = st.toggle("Show already-remediated items", value=False, key="remedy_show_all")

    # ── Load failed traces ────────────────────────────────────────────────────
    try:
        param = f"?include_remediated={'true' if show_remediated else 'false'}"
        traces: list[dict] = _get(f"/api/v1/traces/{audit_id}/failed{param}", token)
    except requests.HTTPError as e:
        st.error(f"Failed to load traces: {e}")
        return

    if not traces:
        if show_remediated:
            st.info("No failed traces found for this audit.")
        else:
            st.info("No pending issues — all items have been remediated.")
        return

    # ── Group by gate ─────────────────────────────────────────────────────────
    by_gate: dict[str, list[dict]] = {}
    for t in traces:
        gate_key = f"Gate {t['gate_id']}: {t['gate_name']}"
        by_gate.setdefault(gate_key, []).append(t)

    result_icons = {
        "fail": "❌",
        "warn": "⚠️",
        "flagged": "🚩",
        "triggered": "📋",
        "pass": "✅",
    }
    result_colors = {
        "fail": "red",
        "warn": "orange",
        "flagged": "red",
        "triggered": "blue",
        "pass": "green",
    }

    for gate_name, gate_traces in by_gate.items():
        failed_count = sum(1 for t in gate_traces if not t["is_remediated"])
        remediated_count = sum(1 for t in gate_traces if t["is_remediated"])

        st.subheader(f"{gate_name}  —  {len(gate_traces)} issue(s)")

        for trace in gate_traces:
            result = trace["result"]
            icon = result_icons.get(result, "•")
            color = result_colors.get(result, "grey")
            remediated_badge = " — ✅ *Remediated*" if trace["is_remediated"] else ""

            expander_label = (
                f"{icon} **{trace['check_name'][:80]}** "
                f"— :{color}[{result.upper()}]{remediated_badge}"
            )

            with st.expander(expander_label, expanded=(not trace["is_remediated"] and result in ("fail", "flagged"))):
                # Detail columns
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("**What was checked:**")
                    st.write(trace["check_name"])

                    if trace.get("reason"):
                        st.markdown("**Why it failed / what was detected:**")
                        st.write(trace["reason"])

                    if trace.get("remediation_hint"):
                        st.markdown("**Suggested remediation:**")
                        st.info(trace["remediation_hint"])

                with c2:
                    st.markdown(f"**Gate:** {trace['gate_id']} — {trace['gate_name'][:30]}")
                    st.markdown(f"**Check type:** `{trace['check_type']}`")
                    st.markdown(f"**Result:** :{color}[{result.upper()}]")
                    if trace.get("remediated_at"):
                        st.markdown(f"**Remediated:** {trace['remediated_at'][:19]}")

                if trace.get("detail_json"):
                    with st.expander("Raw detail data", expanded=False):
                        st.json(trace["detail_json"])

                # ── Remediate action ──────────────────────────────────────────
                if not trace["is_remediated"]:
                    st.divider()
                    form_key = f"remedy_form_{trace['id']}"
                    with st.form(form_key):
                        notes = st.text_area(
                            "Remediation notes (optional)",
                            placeholder="Describe what action was taken...",
                            key=f"notes_{trace['id']}",
                            height=80,
                        )
                        submitted = st.form_submit_button(
                            "✅ Mark as Remediated",
                            use_container_width=True,
                            type="primary",
                        )

                    if submitted:
                        try:
                            _post(
                                f"/api/v1/traces/{audit_id}/{trace['id']}/remediate",
                                token,
                                {"notes": notes or None},
                            )
                            st.success(f"✅ Marked as remediated.")
                            st.rerun()
                        except requests.HTTPError as e:
                            st.error(f"Failed to update: {e}")

        st.divider()
