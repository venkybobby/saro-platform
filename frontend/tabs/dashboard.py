"""
SARO Enterprise Audit Dashboard Tab
=====================================
Screens:
  - KPI summary bar   (total audits, avg risk, pending remediations, coverage)
  - Risk trend chart  (30-day rolling risk score — Plotly line chart)
  - Audit table       (sortable/filterable, risk colour-coded, exception counts)
  - Audit detail      (4 tabs: Overview | Findings | TRACE | REMEDIATE)
    - TRACE: full, untruncated chain-of-thought timeline + executive/technical toggle
"""
from __future__ import annotations

import json
from typing import Any

import plotly.graph_objects as go
import requests
import streamlit as st

_RISK_COLORS = {"green": "#16a34a", "yellow": "#ca8a04", "red": "#dc2626"}
_RISK_LABELS = {"green": "LOW RISK", "yellow": "MODERATE RISK", "red": "HIGH RISK"}
_RESULT_BADGE = {
    "pass":      ("✓", "#16a34a"),
    "warn":      ("⚠", "#ca8a04"),
    "fail":      ("✗", "#dc2626"),
    "flagged":   ("⚑", "#dc2626"),
    "triggered": ("!", "#9333ea"),
}


def _api(token: str, method: str, path: str, **kwargs: Any) -> requests.Response:
    base = st.session_state.get("api_base", "http://localhost:8000").rstrip("/")
    return getattr(requests, method)(
        f"{base}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        **kwargs,
    )


def _safe_get(token: str, path: str) -> dict | list | None:
    try:
        resp = _api(token, "get", path)
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
        delta=None,
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
    # Reference bands
    fig.add_hrect(y0=85, y1=100, fillcolor="#16a34a", opacity=0.06, line_width=0, annotation_text="Low Risk", annotation_position="right")
    fig.add_hrect(y0=50, y1=85, fillcolor="#ca8a04", opacity=0.06, line_width=0, annotation_text="Moderate", annotation_position="right")
    fig.add_hrect(y0=0, y1=50, fillcolor="#dc2626", opacity=0.06, line_width=0, annotation_text="High Risk", annotation_position="right")

    fig.update_layout(
        title="30-Day Risk Score Trend",
        xaxis_title="Date",
        yaxis_title="Risk Score (0–100)",
        yaxis=dict(range=[0, 100]),
        height=280,
        margin=dict(l=0, r=80, t=40, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Audit Table ───────────────────────────────────────────────────────────────


def _risk_badge_html(color: str | None, score: float | None) -> str:
    if color is None or score is None:
        return "—"
    c = _RISK_COLORS.get(color, "#6b7280")
    label = _RISK_LABELS.get(color, "—")
    return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:600">{score:.0f} {label}</span>'


def _render_audit_table(audits: list[dict[str, Any]]) -> int | None:
    """Render the sortable audit table. Returns selected audit index or None."""
    if not audits:
        st.info("No audits found. Run your first audit from the Upload & Scan tab.")
        st.button("Go to Upload & Scan →", type="primary")
        return None

    # Filters
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search = st.text_input("Search by dataset name", placeholder="Filter audits…", label_visibility="collapsed")
    with col_f2:
        status_filter = st.selectbox(
            "Status", ["All", "completed", "failed", "pending", "running"], label_visibility="collapsed"
        )
    with col_f3:
        risk_filter = st.selectbox(
            "Risk Level", ["All", "Low Risk (≥85)", "Moderate (50–84)", "High Risk (<50)"],
            label_visibility="collapsed",
        )

    # Apply filters
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

    # Table header
    h1, h2, h3, h4, h5, h6, h7 = st.columns([2.5, 1.2, 1.5, 0.9, 0.9, 0.9, 0.8])
    h1.markdown("**Dataset**")
    h2.markdown("**Date**")
    h3.markdown("**Risk Score**")
    h4.markdown("**Status**")
    h5.markdown("**Exceptions**")
    h6.markdown("**Remediated**")
    h7.markdown("**Action**")
    st.divider()

    selected: int | None = None
    for idx, audit in enumerate(filtered):
        score = audit.get("overall_risk_score")
        color = audit.get("risk_color")
        exceptions = audit.get("exceptions_count", 0)
        remediated = audit.get("remediated_count", 0)
        status = audit.get("status", "—")
        dataset = audit.get("dataset_name") or "Unnamed Dataset"
        created = (audit.get("created_at") or "")[:10]
        rem_badge = " 🔴" if audit.get("remediation_required") else ""

        status_icon = {"completed": "✅", "failed": "❌", "pending": "⏳", "running": "🔄"}.get(status, "—")

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
        c4.markdown(f"{status_icon} {status}")
        c5.markdown(str(exceptions))
        c6.markdown(f"{remediated}/{exceptions}" if exceptions else "—")
        with c7:
            if st.button("View", key=f"view_audit_{idx}", use_container_width=True):
                selected = idx

    return selected


# ── TRACE View ────────────────────────────────────────────────────────────────


def _render_trace_view(token: str, audit_id: str, dataset_name: str) -> None:
    st.markdown("### TRACE — AI Explainability")
    st.caption(f"Full, untruncated chain-of-thought for audit `{audit_id}`")

    with st.spinner("Loading trace data…"):
        trace = _safe_get(token, f"/api/v1/dashboard/audits/{audit_id}/trace")

    if not trace:
        st.error("Trace data unavailable for this audit.")
        return

    # Confidence badge
    conf = trace.get("confidence")
    conf_color = "#16a34a" if (conf or 0) >= 0.9 else ("#ca8a04" if (conf or 0) >= 0.7 else "#dc2626")
    conf_label = f"Confidence: {conf:.1%}" if conf is not None else "Confidence: N/A"
    st.markdown(
        f'<div style="display:inline-block;background:{conf_color};color:#fff;'
        f'padding:4px 14px;border-radius:20px;font-weight:700;font-size:0.9rem;margin-bottom:12px">'
        f'{conf_label}</div>',
        unsafe_allow_html=True,
    )

    # Executive ↔ Technical toggle
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
        _render_trace_technical(trace, audit_id)


def _render_trace_executive(trace: dict[str, Any]) -> None:
    """Concise executive summary — facts, no jargon."""
    summary = trace.get("executive_summary") or "No executive summary available."
    st.markdown("#### Executive Summary")
    st.text(summary)  # preserves newlines, no markdown injection

    cot = trace.get("chain_of_thought", {})
    steps = cot.get("steps", [])
    total = cot.get("total_checks", 0)
    failed = cot.get("failed_checks", 0)

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Checks", total)
    col2.metric("Exceptions", failed)
    col3.metric("Gates", cot.get("gate_count", len(steps)))

    # Compact gate status row
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

    # Export
    st.divider()
    _render_export_controls(trace)


def _render_trace_technical(trace: dict[str, Any], audit_id: str) -> None:
    """Full technical deep dive — all gates, all checks, all detail."""
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

            checks = step.get("checks", [])
            for check in checks:
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

                reason = check.get("reason")
                if reason:
                    st.markdown(f"**Reason:** {reason}")

                hint = check.get("remediation_hint")
                if hint:
                    st.markdown(f"**Remediation:** {hint}")

                detail = check.get("detail")
                if detail:
                    with st.expander("Detail JSON"):
                        st.json(detail)

    # Client Input / Output
    st.divider()
    col_in, col_out = st.columns(2)
    with col_in:
        st.markdown("#### Client Input Summary")
        input_summary = trace.get("client_input_summary")
        if input_summary:
            st.json(input_summary)
        else:
            st.caption("Not available")

    with col_out:
        st.markdown("#### Client Output Summary")
        output_summary = trace.get("client_output_summary")
        if output_summary:
            st.json(output_summary)
        else:
            st.caption("Not available")

    # Raw Prompt / Response (expandable)
    st.divider()
    raw_prompt = trace.get("raw_prompt")
    raw_response = trace.get("raw_response")

    col_p, col_r = st.columns(2)
    with col_p:
        with st.expander("Raw Audit Prompt"):
            if raw_prompt:
                st.code(raw_prompt, language=None)
            else:
                st.caption("Not stored")
    with col_r:
        with st.expander("Raw Pipeline Response"):
            if raw_response:
                st.code(raw_response, language="json")
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

    # Header
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
        _render_trace_view(token, audit_id, dataset)

    with tab_remediate:
        _render_audit_remediate(token, audit)


def _render_audit_overview(audit: dict[str, Any]) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Audit ID**")
        st.code(str(audit["id"]), language=None)
        st.markdown(f"**Created:** {(audit.get('created_at') or '')[:19].replace('T', ' ')} UTC")
        completed = audit.get("completed_at")
        if completed:
            st.markdown(f"**Completed:** {completed[:19].replace('T', ' ')} UTC")
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

    # Group by gate
    by_gate: dict[str, list] = {}
    for t in traces:
        gate_key = f"Gate {t['gate_id']}: {t['gate_name']}"
        by_gate.setdefault(gate_key, []).append(t)

    for gate_key, gate_traces in sorted(by_gate.items()):
        failed_in_gate = sum(1 for t in gate_traces if t["result"] in ("fail", "warn", "flagged", "triggered"))
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
                    f'<b style="color:{color}">{icon} {result.upper()}</b> — {t.get("check_name", "")} '
                    f'<span style="color:#16a34a;font-size:0.8rem">{remediated}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                reason = t.get("reason")
                if reason:
                    st.caption(f"  {reason[:300]}{'…' if len(reason or '') > 300 else ''}")


def _render_audit_remediate(token: str, audit: dict[str, Any]) -> None:
    audit_id = str(audit["id"])
    exceptions = audit.get("exceptions_count", 0)
    remediated_count = audit.get("remediated_count", 0)
    pending = exceptions - remediated_count

    if exceptions == 0:
        st.success("No exceptions detected in this audit — nothing to remediate.")
        return

    if pending == 0:
        st.success(f"All {exceptions} exception(s) have been remediated.")
        if st.button("Show remediated items"):
            pass  # falls through to load all below

    st.markdown(f"### {pending} Remediation(s) Required")

    show_all = st.toggle("Show already-remediated items", value=False)
    endpoint = f"/api/v1/traces/{audit_id}" + ("" if show_all else "/failed")
    traces = _safe_get(token, endpoint)
    if not traces:
        st.info("No items found.")
        return

    # Priority sort: fail > flagged > triggered > warn
    priority_order = {"fail": 0, "flagged": 1, "triggered": 2, "warn": 3}
    traces = sorted(traces, key=lambda t: priority_order.get(t.get("result", ""), 99))

    for t in traces:
        result = t.get("result", "pass")
        icon, color = _RESULT_BADGE.get(result, ("?", "#6b7280"))
        is_rem = t.get("is_remediated", False)

        severity_map = {"fail": "CRITICAL", "flagged": "HIGH", "triggered": "HIGH", "warn": "MEDIUM"}
        severity = severity_map.get(result, "LOW")

        with st.expander(
            f"{icon} [{severity}] {t.get('check_name', '')} — "
            f"{'✅ Remediated' if is_rem else 'Pending'}",
            expanded=not is_rem,
        ):
            st.markdown(f"**Gate:** {t.get('gate_name', '')} (Gate {t.get('gate_id', '')})")
            st.markdown(f"**Result:** {result.upper()}")

            reason = t.get("reason") or "—"
            st.markdown("**Finding:**")
            st.text(reason)

            hint = t.get("remediation_hint")
            if hint:
                st.info(f"**AI Fix Suggestion:** {hint}", icon="💡")

            detail = t.get("detail_json")
            if detail:
                with st.expander("Technical detail"):
                    st.json(detail)

            if is_rem:
                rem_at = (t.get("remediated_at") or "")[:19]
                st.success(f"Remediated: {rem_at}")
            else:
                notes = st.text_area(
                    "Remediation notes",
                    key=f"rem_notes_{t['id']}",
                    placeholder="Describe the corrective action taken…",
                    height=80,
                )
                col_act, col_jira = st.columns([1, 1])
                with col_act:
                    if st.button("Mark Resolved", key=f"rem_btn_{t['id']}", type="primary"):
                        try:
                            resp = _api(
                                st.session_state.get("auth_token", ""),
                                "post",
                                f"/api/v1/traces/{audit_id}/{t['id']}/remediate",
                                json={"notes": notes or None},
                            )
                            resp.raise_for_status()
                            st.success("Marked as remediated.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Failed to update: {exc}")
                with col_jira:
                    st.button(
                        "Create Jira Ticket",
                        key=f"jira_{t['id']}",
                        help="Jira integration — configure in Settings",
                        disabled=True,
                    )


# ── Main render ───────────────────────────────────────────────────────────────


def render(token: str) -> None:
    st.session_state["auth_token"] = token  # stored for remediation buttons

    st.header("Audit Dashboard")
    st.caption(
        "Enterprise-grade view of all AI risk audits. "
        "Click any audit to drill into findings, trace, and remediation."
    )

    # Load KPIs
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

    # Track selected audit in session state
    if "dashboard_selected_audit" not in st.session_state:
        st.session_state["dashboard_selected_audit"] = None

    selected_idx = _render_audit_table(audits)
    if selected_idx is not None:
        st.session_state["dashboard_selected_audit"] = selected_idx

    selected = st.session_state.get("dashboard_selected_audit")
    if selected is not None and audits:
        # Apply same filter to get correct audit — use full list for detail lookup
        audit_detail = audits[selected] if selected < len(audits) else None
        if audit_detail:
            st.divider()
            with st.container():
                close_col, _ = st.columns([1, 5])
                with close_col:
                    if st.button("✕ Close Detail"):
                        st.session_state["dashboard_selected_audit"] = None
                        st.rerun()
                _render_audit_detail(token, audit_detail)
