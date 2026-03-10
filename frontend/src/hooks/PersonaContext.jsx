/**
 * SARO — Persona RBAC Context & Provider
 * ========================================
 * Single source of truth for persona-based screen restrictions.
 * Wraps the entire app; gates every nav item and route.
 *
 * Integrates with your existing auth endpoints:
 *   POST /auth/magic-link → returns persona + token
 *   GET  /auth/validate   → returns session with persona
 *   GET  /auth/me         → returns current session
 *
 * Personas: forecaster, autopsier, enabler, evangelist
 * Admin: is_admin flag bypasses all restrictions
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";

const API = import.meta.env.VITE_API_URL || "";

// ─── Persona → Allowed Screens Matrix ─────────────────────────────
// Maps directly to FR-005 from the spec. Each persona sees ONLY these screens.
const PERSONA_SCREENS = {
  forecaster: {
    label: "Forecaster",
    icon: "📈",
    color: "#06b6d4",       // cyan
    screens: ["mvp1", "mvp3", "dashboard"],
    features: ["forecast", "risk-trends", "regulations", "scenario-modeler"],
    description: "Regulatory intelligence, risk prediction, scenario modeling",
    defaultPage: "mvp1",
    metrics: [
      { key: "forecast_accuracy", label: "Forecast Accuracy", value: "85%", target: "85%", tooltip: "Gap forecast precision vs. NIST benchmarks" },
      { key: "gap_preempt",       label: "Gap Preempt Rate",  value: "40%", target: "50%", tooltip: "Gaps identified before becoming violations" },
      { key: "ci_width",          label: "CI Width",          value: "±12%",target: "<±15%",tooltip: "Bayesian prediction confidence interval" },
      { key: "sim_runtime",       label: "Sim Runtime",       value: "8.2s",target: "<10s", tooltip: "Average 6-12mo simulation time" },
    ],
  },
  autopsier: {
    label: "Autopsier",
    icon: "🔍",
    color: "#f59e0b",       // amber
    screens: ["auditflow", "audit-explorer", "compliance-map"],
    features: ["audit", "evidence", "checklist", "standards-map", "audit-db"],
    description: "Deep-dive audit findings, evidence chains, compliance verification",
    defaultPage: "auditflow",
    metrics: [
      { key: "alert_precision",  label: "Alert Precision",    value: "88%",   target: "85%",  tooltip: "True positive rate for compliance alerts" },
      { key: "false_positive",   label: "False Positive Rate", value: "4.2%",  target: "<5%",  tooltip: "Incorrect alerts — lower = less noise" },
      { key: "mitigation_rate",  label: "Mitigation Rate",    value: "70%",   target: "70%",  tooltip: "Critical findings with active mitigation plans" },
      { key: "evidence_chain",   label: "Evidence Integrity",  value: "99.8%", target: "99.5%",tooltip: "Audit records with valid hash chains" },
    ],
  },
  enabler: {
    label: "Enabler",
    icon: "⚙️",
    color: "#22c55e",       // green
    screens: ["mvp3", "mvp4", "onboarding", "integrations", "training"],
    features: ["remediation", "upload", "onboard-manage", "policy-engine"],
    description: "Implement controls, manage policies, drive remediation",
    defaultPage: "mvp4",
    metrics: [
      { key: "effort_days",       label: "Avg Effort Days",       value: "3.2",   target: "<5",    tooltip: "Days to resolve a critical compliance finding" },
      { key: "impact_score",      label: "Impact Score",          value: "8.4/10",target: ">7.5",  tooltip: "Remediation effectiveness across risk categories" },
      { key: "roi_savings",       label: "ROI Savings",           value: "$150K", target: ">$100K",tooltip: "Fine avoidance + reduced audit costs" },
      { key: "critical_reduction",label: "Critical Findings ↓",   value: "70%",   target: "70%",   tooltip: "Reduction in critical-severity findings" },
    ],
  },
  evangelist: {
    label: "Evangelist",
    icon: "🎯",
    color: "#a855f7",       // purple
    screens: ["dashboard", "ethics", "reports", "executive"],
    features: ["ethics-report", "bias-review", "public-docs", "trust-metrics", "board-report"],
    description: "Executive summaries, ROI metrics, board reporting, ethics overview",
    defaultPage: "dashboard",
    metrics: [
      { key: "nps_score",        label: "Trust NPS",           value: "78",   target: ">75",  tooltip: "Stakeholder Net Promoter Score on AI trust" },
      { key: "compliance_score", label: "Compliance Coverage",  value: "82%",  target: ">80%", tooltip: "EU/ISO/NIST controls mapped and evidenced" },
      { key: "trust_uplift",     label: "Trust Uplift",        value: "70%",  target: ">65%", tooltip: "Stakeholder confidence improvement" },
      { key: "report_gen_time",  label: "Report Gen Time",     value: "4.1s", target: "<5s",  tooltip: "Standards-aligned PDF report generation" },
    ],
  },
};

// Admin has access to everything plus admin-only screens
const ADMIN_SCREENS = ["admin", "provisioning", "tenant-config", "billing"];

// ─── Context ──────────────────────────────────────────────────────
const PersonaContext = createContext(null);

export function PersonaProvider({ children }) {
  const [session, setSession] = useState(null);       // full session from /auth/validate
  const [persona, setPersona] = useState(null);        // current active persona string
  const [personaDef, setPersonaDef] = useState(null);  // PERSONA_SCREENS[persona]
  const [roles, setRoles] = useState([]);              // all assigned roles (multi-role)
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ── Load session on mount ───────────────────────────────────────
  const loadSession = useCallback(async (token) => {
    try {
      setLoading(true);
      setError(null);

      // Try /auth/validate if we have a token, else /auth/me
      const url = token
        ? `${API}/api/v1/auth/validate?token=${token}`
        : `${API}/api/v1/auth/me`;
      const headers = token ? {} : {
        Authorization: `Bearer ${localStorage.getItem("saro_token") || ""}`,
      };

      const res = await fetch(url, { headers });
      if (!res.ok) throw new Error("Session invalid");
      const data = await res.json();

      const activePersona = data.persona || "enabler";
      const userRoles = data.roles || [activePersona];
      const admin = data.is_admin || false;

      setSession(data);
      setPersona(activePersona);
      setPersonaDef(PERSONA_SCREENS[activePersona] || PERSONA_SCREENS.enabler);
      setRoles(userRoles);
      setIsAdmin(admin);

      // Store token for subsequent requests
      if (data.token) {
        localStorage.setItem("saro_token", data.token);
      }

      return data;
    } catch (e) {
      setError(e.message);
      setSession(null);
      setPersona(null);
      setPersonaDef(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Check URL for magic link token on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      loadSession(token);
      // Clean URL
      window.history.replaceState({}, "", window.location.pathname);
    } else {
      loadSession(null);
    }
  }, [loadSession]);

  // ── Screen access check ─────────────────────────────────────────
  const canAccessScreen = useCallback((screenId) => {
    if (!persona) return false;
    if (isAdmin) return true;

    // Check all assigned roles (multi-role merge)
    for (const role of roles) {
      const def = PERSONA_SCREENS[role];
      if (def && def.screens.includes(screenId)) return true;
    }
    return false;
  }, [persona, isAdmin, roles]);

  // ── Feature access check ────────────────────────────────────────
  const canAccessFeature = useCallback((featureId) => {
    if (!persona) return false;
    if (isAdmin) return true;

    for (const role of roles) {
      const def = PERSONA_SCREENS[role];
      if (def && def.features.includes(featureId)) return true;
    }
    return false;
  }, [persona, isAdmin, roles]);

  // ── Get all allowed screens (merged across roles) ───────────────
  const getAllowedScreens = useCallback(() => {
    if (isAdmin) {
      const all = new Set();
      Object.values(PERSONA_SCREENS).forEach(d => d.screens.forEach(s => all.add(s)));
      ADMIN_SCREENS.forEach(s => all.add(s));
      return [...all];
    }
    const screens = new Set();
    for (const role of roles) {
      const def = PERSONA_SCREENS[role];
      if (def) def.screens.forEach(s => screens.add(s));
    }
    return [...screens];
  }, [isAdmin, roles]);

  // ── Role switching (multi-role) ─────────────────────────────────
  const switchRole = useCallback((newRole) => {
    if (!roles.includes(newRole) && !isAdmin) {
      console.warn(`Cannot switch to ${newRole} — not assigned`);
      return false;
    }
    const def = PERSONA_SCREENS[newRole];
    if (!def) return false;
    setPersona(newRole);
    setPersonaDef(def);
    return true;
  }, [roles, isAdmin]);

  // ── Login helper ────────────────────────────────────────────────
  const login = useCallback(async (email, selectedPersona) => {
    try {
      setLoading(true);
      const res = await fetch(`${API}/api/v1/auth/magic-link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, persona: selectedPersona }),
      });
      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();
      if (data.token) {
        return loadSession(data.token);
      }
      return data;
    } catch (e) {
      setError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [loadSession]);

  // ── Logout ──────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await fetch(`${API}/api/v1/auth/logout`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${localStorage.getItem("saro_token")}` },
      });
    } catch (e) { /* ok */ }
    localStorage.removeItem("saro_token");
    setSession(null);
    setPersona(null);
    setPersonaDef(null);
    setRoles([]);
    setIsAdmin(false);
  }, []);

  const value = {
    // State
    session,
    persona,
    personaDef,
    roles,
    isAdmin,
    loading,
    error,
    // Screen/feature gating
    canAccessScreen,
    canAccessFeature,
    getAllowedScreens,
    // Actions
    switchRole,
    login,
    logout,
    loadSession,
    // Static config
    PERSONA_SCREENS,
    ADMIN_SCREENS,
  };

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
}

export function usePersona() {
  const ctx = useContext(PersonaContext);
  if (!ctx) throw new Error("usePersona must be used within PersonaProvider");
  return ctx;
}

export { PERSONA_SCREENS, ADMIN_SCREENS };
export default PersonaContext;
