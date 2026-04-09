"""
SARO Enterprise Audit Dashboard Tab
=====================================
Screens:
  - KPI summary bar   (total audits, avg risk, pending remediations, coverage)
  - Risk trend chart  (30-day rolling risk score)
  - Audit table       (filterable, risk colour-coded, exception counts)
  - Audit detail      (4 sub-tabs: Overview | Findings | TRACE | REMEDIATE)
    - TRACE: full, untruncated chain-of-thought timeline
    - REMEDIATE: operator remediation workflow
"""
from __future__ import annotations

import json
import os
from typing import Any

import plotly.graph_objects as go
import requests
import streamlit as st

_API_BASE = os.environ.get("SARO_API_URL", "http://localhost:8000").rstrip("/")

_RISK_COLORS = {"green": "#16a34a", "yellow": "#ca8a04", "red": "#dc2626"}
_RISK_LABELS = {"green": "LOW RISK", "yellow": "MODERATE RISK", "red": "HIGH RISK"}
_RESULT_BADGE = {
    "pass":      ("✓", "#16a34a"),
    "warn":      ("⚠", "#ca8a04"),
    "fail":      ("✗", "#dc2626"),
    "flagged":   ("⚑", "#dc2626"),
    "triggered": ("!", "#9333ea"),
}


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _safe_get(token: str, path: str) -> dict | list | None:
    try:
        resp = requests.get(
            f"{_API_BASE}{path}",
            headers=_headers(token),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"API error ({path}): {exc}")
        return None


def _safe_post(token: str, path: str, json_body: dict) -> dict | None:
    try:
        resp = requests.post(
            f"{_API_BASE}{path}",
            headers=_headers(token),
            json=json_body,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"API error ({path}): {exc}")
        return None


# ── KPI Bar ───────────────────────────────────────────────────────────────────


def _render_kpi_bar(kpis: dict[str, Any]) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Audits", kpis.get("total_audits", 0))
    c2.metric("Completed", kpis.get("completed_audits", 0))
    c3.metric(
        "Avg Risk Score",
        f"{kpis['avg_risk_score']:.1f}" if kpis.get("avg_risk_score") is not None else "—",
        help="Higher = lower risk. ≥85 = Low Risk, 50–84 = Moderate, <50 = High.",
    )
    c4.metric(
        "Avg MIT Coverage",
        f"{kpis['avg_mit_coverage']:.1f}%" if kpis.get("avg_mit_coverage") is not None else "—",
    )
    c5.metric(
        "Pending Remediations",
        kpis.get("pending_remediations", 0),
        delta_color="inverse",
    )


# ── Risk Trend Chart ──────────────────────────────────────────────────────────


def _render_risk_trend(trend: list[dict[str, Any]]) -> None:
    if not trend:
        st.info("No completed audits in the last 30 days — trend chart will populate as audits complete.")
        return

    dates = [t["date"] for t in trend]
    scores = [t["avg_risk_score"] for t in trend]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="Avg Risk Score",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>Risk Score: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_hrect(y0=85, y1=100, fillcolor="#16a34a", opacity=0.06, line_width=0,
                  annotation_text="Low Risk", annotation_position="right")
    fig.add_hrect(y0=50, y1=85, fillcolor="#ca8a04", opacity=0.06, line_width=0,
                  annotation_text="Moderate", annotation_position="right")
    fig.add_hrect(y0=0, y1=50, fillcolor="#dc2626", opacity=0.06, line_width=0,
                  annotation_text="High Risk", annotation_position="right")

    fig.update_layout(
        title="30-Day Risk Score Trend",
        xaxis_title="Date",
        yaxis_title="Risk Score (0–100)",
        yaxis=dict(range=[0, 100]),
        height=280,
        margin=dict(l=0, r=80, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Audit Table ───────────────────────────────────────────────────────────────


def _render_audit_table(audits: list[dict[str, Any]]) -> int | None:
    if not audits:
        st.info("No audits found. Run your first audit from the Upload & Scan tab.")
        return None

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search = st.text_input("Search by dataset name", placeholder="Filter audits…",
                               label_visibility="collapsed")
    with col_f2:
        status_filter = st.selectbox(
            "Status", ["All", "completed", "failed", "pending", "running"],
            label_visibility="collapsed",
        )
    with col_f3:
        risk_filter = st.selectbox(
            "Risk Level", ["All", "Low Risk (≥85)", "Moderate (50–84)", "High Risk (<50)"],
            label_visibility="collapsed",
        )

    filtered = audits
    if search:
        filtered = [a for a in filtered if search.lower() in (a.get("dataset_name") or "").lower()]
    if status_filter != "All":
        filtered = [a for a in filtered if a.get("status") == status_filter]
    if risk_filter != "All":
        if risk_filter.startswith("Low"):
            filtered = [a for a in filtered if (a.get("overall_risk_score") or 0) >= 85]
        elif risk_filter.startswith("Moderate"):
            filtered = [a for a in filtered if 50 <= (a.get("overall_risk_score") or 0) < 85]
        elif risk_filter.startswith("High"):
            filtered = [a for a in filtered if 0 < (a.get("overall_risk_score") or 101) < 50]

    st.caption(f"Showing {len(filtered)} of {len(audits)} audit(s)")

    h1, h2, h3, h4, h5, h6, h7 = st.columns([2.5, 1.2, 1.5, 0.9, 0.9, 0.9, 0.8])
    h1.markdown("**Dataset**")
    h2.markdown("**Date**")
    h3.markdown("**Risk Score**")
    h4.markdown("**Status**")
    h5.markdown("**Exceptions**")
    h6.markdown("**Remediated**")
    h7.markdown("**Action**")
    st.divider()

    # Store filtered list for detail lookup
    st.session_state["_dashboard_filtered_audits"] = filtered

    selected: int | None = None
    for idx, audit in enumerate(filtered):
        score = audit.get("overall_risk_score")
        color = audit.get("risk_color")
        exceptions = audit.get("exceptions_count", 0)
        remediated = audit.get("remediated_count", 0)
        audit_status = audit.get("status", "—")
        dataset = audit.get("dataset_name") or "Unnamed Dataset"
        created = (audit.get("created_at") or "")[:10]
        rem_badge = " 🔴" if audit.get("remediation_required") else ""

        status_icon = {"completed": "✅", "failed": "❌", "pending": "⏳", "running": "🔄"}.get(
            audit_status, "—"
        )

        c1, c2, c3, c4, c5, c6, c7 = st.columns([2.5, 1.2, 1.5, 0.9, 0.9, 0.9, 0.8])
        c1.markdown(f"**{dataset}**{rem_badge}")
        c2.markdown(created)
        if score is not None and color:
            hex_c = _RISK_COLORS.get(color, "#6b7280")
            c3.markdown(
                f'<span style="background:{hex_c};color:#fff;padding:1px 7px;border-radius:4px;'
                f'font-size:0.8rem;font-weight:600">{score:.1f}</span>',
                unsafe_allow_html=True,
            )
        else:
            c3.markdown("—")
        c4.markdown(f"{status_icon} {audit_status}")
        c5.markdown(str(exceptions))
        c6.markdown(f"{remediated}/{exceptions}" if exceptions else "—")
        with c7:
            if st.button("View", key=f"view_audit_{idx}", use_container_width=True):
                selected = idx

    return selected


# ── TRACE View ────────────────────────────────────────────────────────────────


def _render_trace_view(token: str, audit_id: str) -> None:
    st.markdown("### TRACE — AI Explainability & Chain-of-Thought")
    st.caption(
        f"Full, untruncated audit trail for `{audit_id}` — zero truncation, zero ambiguity."
    )

    with st.spinner("Loading trace data…"):
        trace = _safe_get(token, f"/api/v1/dashboard/audits/{audit_id}/trace")

    if not trace:
        st.warning(
            "Trace data unavailable for this audit. "
            "Traces are stored for audits run after v2.0."
        )
        return

    conf = trace.get("confidence")
    conf_color = "#16a34a" if (conf or 0) >= 0.9 else ("#ca8a04" if (conf or 0) >= 0.7 else "#dc2626")
    conf_label = f"Confidence: {conf:.1%}" if conf is not None else "Confidence: N/A"
    st.markdown(
        f'<div style="display:inline-block;background:{conf_color};color:#fff;'
        f'padding:4px 14px;border-radius:20px;font-weight:700;font-size:0.9rem;margin-bottom:12px">'
        f'{conf_label}</div>',
        unsafe_allow_html=True,
    )

    view_mode = st.radio(
        "View Mode",
        ["Executive Summary", "Technical Deep Dive"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.divider()

    if view_mode == "Executive Summary":
        _render_trace_executive(trace)
    else:
        _render_trace_technical(trace)


def _render_trace_executive(trace: dict[str, Any]) -> None:
    summary = trace.get("executive_summary") or "No executive summary available."
    st.markdown("#### Executive Summary")
    st.text(summary)

    cot = trace.get("chain_of_thought", {})
    steps = cot.get("steps", [])
    total = cot.get("total_checks", 0)
    failed = cot.get("failed_checks", 0)

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checks", total)
    col2.metric("Exceptions", failed)
    col3.metric("Gates", cot.get("gate_count", len(steps)))

    if steps:
        st.markdown("#### Gate Summary")
        gate_cols = st.columns(len(steps))
        for i, step in enumerate(steps):
            with gate_cols[i]:
                result = step.get("result", "pass")
                icon, color = _RESULT_BADGE.get(result, ("?", "#6b7280"))
                st.markdown(
                    f'<div style="text-align:center;padding:12px;border:1px solid {color};'
                    f'border-radius:8px;background:{color}18">'
                    f'<div style="font-size:1.5rem">{icon}</div>'
                    f'<div style="font-weight:700;font-size:0.8rem;color:{color}">{result.upper()}</div>'
                    f'<div style="font-size:0.75rem;margin-top:4px">{step.get("gate", "")}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.divider()
    _render_export_controls(trace)


def _render_trace_technical(trace: dict[str, Any]) -> None:
    cot = trace.get("chain_of_thought", {})
    steps = cot.get("steps", [])

    st.markdown("#### Chain-of-Thought Timeline")

    for step in steps:
        gate_result = step.get("result", "pass")
        icon, color = _RESULT_BADGE.get(gate_result, ("?", "#6b7280"))
        failed_count = step.get("failed_count", 0)
        passed_count = step.get("passed_count", 0)

        with st.expander(
            f"{icon} Gate {step['step']} — {step.get('gate', '')}   "
            f"[{passed_count} passed · {failed_count} failed]",
            expanded=(gate_result != "pass"),
        ):
            ts = step.get("timestamp")
            if ts:
                st.caption(f"Executed: {ts[:19].replace('T', ' ')} UTC")

            for check in step.get("checks", []):
                c_result = check.get("result", "pass")
                c_icon, c_color = _RESULT_BADGE.get(c_result, ("?", "#6b7280"))
                st.markdown(
                    f'<div style="border-left:3px solid {c_color};padding:6px 12px;'
                    f'margin:6px 0;background:{c_color}0a;border-radius:0 6px 6px 0">'
                    f'<span style="font-weight:700;color:{c_color}">{c_icon} {c_result.upper()}</span>'
                    f' — <span style="font-weight:600">{check.get("name", "")}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if check.get("reason"):
                    st.markdown(f"**Reason:** {check['reason']}")
                if check.get("remediation_hint"):
                    st.markdown(f"**Remediation:** {check['remediation_hint']}")
                if check.get("detail"):
                    with st.expander("Detail JSON"):
                        st.json(check["detail"])

    st.divider()
    col_in, col_out = st.columns(2)
    with col_in:
        st.markdown("#### Client Input Summary")
        st.json(trace.get("client_input_summary") or {})
    with col_out:
        st.markdown("#### Client Output Summary")
        st.json(trace.get("client_output_summary") or {})

    st.divider()
    col_p, col_r = st.columns(2)
    with col_p:
        with st.expander("Raw Audit Prompt"):
            if trace.get("raw_prompt"):
                st.code(trace["raw_prompt"], language=None)
            else:
                st.caption("Not stored")
    with col_r:
        with st.expander("Raw Pipeline Response"):
            if trace.get("raw_response"):
                st.code(trace["raw_response"], language="json")
            else:
                st.caption("Not stored")

    st.divider()
    _render_export_controls(trace)


def _render_export_controls(trace: dict[str, Any]) -> None:
    st.markdown("#### Export")
    col_dl, col_info = st.columns([1, 3])
    with col_dl:
        trace_json = json.dumps(trace, indent=2, default=str)
        st.download_button(
            "Download JSON",
            data=trace_json,
            file_name=f"saro_trace_{trace.get('audit_id', 'unknown')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_info:
        st.caption(
            f"Audit ID: `{trace.get('audit_id')}` · "
            f"Model: `{trace.get('model_version') or 'saro-engine-1.0'}` · "
            f"Generated: {(trace.get('created_at') or '')[:19]}"
        )


# ── Audit Detail Panel ────────────────────────────────────────────────────────


def _render_audit_detail(token: str, audit: dict[str, Any]) -> None:
    audit_id = str(audit["id"])
    dataset = audit.get("dataset_name") or "Unnamed Dataset"
    score = audit.get("overall_risk_score")
    color = audit.get("risk_color")

    st.subheader(f"Audit Detail — {dataset}")
    hcol1, hcol2, hcol3, hcol4 = st.columns(4)
    hcol1.metric("Status", audit.get("status", "—").capitalize())
    if score is not None:
        hex_c = _RISK_COLORS.get(color or "", "#6b7280")
        hcol2.markdown(
            f'**Risk Score**  \n'
            f'<span style="background:{hex_c};color:#fff;padding:3px 10px;border-radius:5px;'
            f'font-weight:700">{score:.1f} — {_RISK_LABELS.get(color or "", "")}</span>',
            unsafe_allow_html=True,
        )
    else:
        hcol2.metric("Risk Score", "—")
    hcol3.metric("MIT Coverage", f"{audit.get('mit_coverage_score') or 0:.1f}%")
    hcol4.metric(
        "Exceptions",
        f"{audit.get('exceptions_count', 0)} ({audit.get('remediated_count', 0)} resolved)",
    )
    st.divider()

    tab_overview, tab_findings, tab_trace, tab_remediate = st.tabs(
        ["Overview", "Findings", "TRACE", "REMEDIATE"]
    )

    with tab_overview:
        _render_audit_overview(audit)

    with tab_findings:
        _render_audit_findings(token, audit_id)

    with tab_trace:
        _render_trace_view(token, audit_id)

    with tab_remediate:
        _render_audit_remediate(token, audit)


def _render_audit_overview(audit: dict[str, Any]) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Audit ID**")
        st.code(str(audit["id"]), language=None)
        st.markdown(f"**Created:** {(audit.get('created_at') or '')[:19].replace('T', ' ')} UTC")
        if audit.get("completed_at"):
            st.markdown(f"**Completed:** {audit['completed_at'][:19].replace('T', ' ')} UTC")
        st.markdown(f"**Confidence:** {audit.get('confidence_score') or 0:.1%}")
    with col2:
        st.markdown("**Remediation Status**")
        exc = audit.get("exceptions_count", 0)
        rem = audit.get("remediated_count", 0)
        pending = exc - rem
        if exc == 0:
            st.success("No exceptions — all gates passed.")
        else:
            st.metric("Pending Remediations", pending)
            if pending > 0:
                st.warning(
                    f"{pending} of {exc} exception(s) require remediation. "
                    "Open the REMEDIATE tab to take action."
                )
            else:
                st.success(f"All {exc} exception(s) remediated.")


def _render_audit_findings(token: str, audit_id: str) -> None:
    st.markdown("#### All Findings")
    traces = _safe_get(token, f"/api/v1/traces/{audit_id}")
    if not traces:
        st.info("No trace records found.")
        return

    by_gate: dict[str, list] = {}
    for t in traces:
        gate_key = f"Gate {t['gate_id']}: {t['gate_name']}"
        by_gate.setdefault(gate_key, []).append(t)

    for gate_key, gate_traces in sorted(by_gate.items()):
        failed_in_gate = sum(
            1 for t in gate_traces
            if t["result"] in ("fail", "warn", "flagged", "triggered")
        )
        with st.expander(
            f"**{gate_key}** — {len(gate_traces)} checks, {failed_in_gate} exception(s)",
            expanded=failed_in_gate > 0,
        ):
            for t in gate_traces:
                result = t.get("result", "pass")
                icon, color = _RESULT_BADGE.get(result, ("?", "#6b7280"))
                remediated = "✅ Remediated" if t.get("is_remediated") else ""
                st.markdown(
                    f'<div style="border-left:3px solid {color};padding:4px 10px;'
                    f'margin:4px 0;background:{color}0d;border-radius:0 4px 4px 0">'
                    f'<b style="color:{color}">{icon} {result.upper()}</b> — '
                    f'{t.get("check_name", "")} '
                    f'<span style="color:#16a34a;font-size:0.8rem">{remediated}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if t.get("reason"):
                    st.caption(f"  {t['reason'][:300]}{'…' if len(t.get('reason', '')) > 300 else ''}")


def _render_audit_remediate(token: str, audit: dict[str, Any]) -> None:
    audit_id = str(audit["id"])
    exceptions = audit.get("exceptions_count", 0)
    remediated_count = audit.get("remediated_count", 0)
    pending = exceptions - remediated_count

    if exceptions == 0:
        st.success("No exceptions detected — all gates passed.")
        return

    if pending == 0:
        st.success(f"All {exceptions} exception(s) have been remediated.")

    st.markdown(f"### {pending} Remediation(s) Required")
    show_all = st.toggle("Show already-remediated items", value=False,
                         key=f"remedy_show_all_{audit_id}")
    endpoint = f"/api/v1/traces/{audit_id}" + ("" if show_all else "/failed")
    traces = _safe_get(token, endpoint)
    if not traces:
        st.info("No items found.")
        return

    priority_order = {"fail": 0, "flagged": 1, "triggered": 2, "warn": 3}
    traces = sorted(traces, key=lambda t: priority_order.get(t.get("result", ""), 99))

    for t in traces:
        result = t.get("result", "pass")
        icon, color = _RESULT_BADGE.get(result, ("?", "#6b7280"))
        is_rem = t.get("is_remediated", False)
        severity = {"fail": "CRITICAL", "flagged": "HIGH", "triggered": "HIGH", "warn": "MEDIUM"}.get(
            result, "LOW"
        )

        with st.expander(
            f"{icon} [{severity}] {t.get('check_name', '')} — "
            f"{'✅ Remediated' if is_rem else 'Pending'}",
            expanded=not is_rem,
        ):
            st.markdown(f"**Gate:** {t.get('gate_name', '')} (Gate {t.get('gate_id', '')})")
            st.markdown(f"**Result:** {result.upper()}")
            st.markdown("**Finding:**")
            st.text(t.get("reason") or "—")

            if t.get("remediation_hint"):
                st.info(f"**AI Fix Suggestion:** {t['remediation_hint']}", icon="💡")

            if t.get("detail_json"):
                with st.expander("Technical detail"):
                    st.json(t["detail_json"])

            if is_rem:
                st.success(f"Remediated: {(t.get('remediated_at') or '')[:19]}")
            else:
                notes = st.text_area(
                    "Remediation notes",
                    key=f"rem_notes_{t['id']}",
                    placeholder="Describe the corrective action taken…",
                    height=80,
                )
                if st.button("Mark Resolved", key=f"rem_btn_{t['id']}", type="primary"):
                    result_data = _safe_post(
                        token,
                        f"/api/v1/traces/{audit_id}/{t['id']}/remediate",
                        {"notes": notes or None},
                    )
                    if result_data is not None:
                        st.success("Marked as remediated.")
                        st.rerun()


# ── Main render ───────────────────────────────────────────────────────────────


def render(token: str) -> None:
    st.header("Audit Dashboard")
    st.caption(
        "Enterprise-grade view of all AI risk audits. "
        "Click any audit to drill into findings, trace, and remediation."
    )

    with st.spinner("Loading dashboard…"):
        kpis = _safe_get(token, "/api/v1/dashboard/kpis")
        audits = _safe_get(token, "/api/v1/dashboard/audits")

    if kpis:
        _render_kpi_bar(kpis)
        st.divider()
        _render_risk_trend(kpis.get("risk_trend", []))
        st.divider()
    else:
        st.warning("KPI data unavailable — check API connectivity.")

    if audits is None:
        st.error("Failed to load audit list.")
        return

    if "dashboard_selected_audit" not in st.session_state:
        st.session_state["dashboard_selected_audit"] = None

    selected_idx = _render_audit_table(audits)
    if selected_idx is not None:
        st.session_state["dashboard_selected_audit"] = selected_idx

    selected = st.session_state.get("dashboard_selected_audit")
    if selected is not None:
        # Use filtered list stored by _render_audit_table for correct index mapping
        filtered = st.session_state.get("_dashboard_filtered_audits", audits)
        audit_detail = filtered[selected] if selected < len(filtered) else None
        if audit_detail:
            st.divider()
            close_col, _ = st.columns([1, 5])
            with close_col:
                if st.button("✕ Close Detail"):
                    st.session_state["dashboard_selected_audit"] = None
                    st.rerun()
            _render_audit_detail(token, audit_detail)
