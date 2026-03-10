/**
 * SARO — Persona RBAC Context & Provider
 * ========================================
 * Reads persona from the EXISTING saro_session in localStorage.
 * No separate auth flow — works with your current Login page.
 *
 * Personas: forecaster, autopsier, enabler, evangelist
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";

// ─── Persona → Allowed Screens Matrix ─────────────────────────────
const PERSONA_SCREENS = {
  forecaster: {
    label: "Forecaster",
    icon: "📈",
    color: "#06b6d4",
    screens: ["mvp1", "dashboard", "feed", "gateway", "platformhealth"],
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
    color: "#f59e0b",
    screens: ["auditflow", "audit-explorer", "compliance-map", "mvp2", "modelchecker", "standards", "reports", "dashboard", "platformhealth"],
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
    color: "#22c55e",
    screens: ["mvp4", "onboarding", "integrations", "training", "mvp3", "mvp5", "policies", "dashboard", "gateway", "platformhealth"],
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
    color: "#a855f7",
    screens: ["dashboard", "ethics", "reports", "executive", "policychat", "gateway", "platformhealth"],
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

const ADMIN_SCREENS = ["admin", "provisioning", "tenant-config", "billing"];

const PersonaContext = createContext(null);

export function PersonaProvider({ children }) {
  const [persona, setPersona] = useState(null);
  const [personaDef, setPersonaDef] = useState(null);
  const [roles, setRoles] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);

  // Read persona from existing saro_session in localStorage
  const syncFromSession = useCallback(() => {
    try {
      const stored = localStorage.getItem('saro_session');
      if (!stored) {
        setPersona(null);
        setPersonaDef(null);
        setRoles([]);
        setIsAdmin(false);
        return;
      }
      const session = JSON.parse(stored);
      const p = session.persona || 'enabler';
      const r = session.roles || [p];
      const admin = session.is_admin || false;

      setPersona(p);
      setPersonaDef(PERSONA_SCREENS[p] || PERSONA_SCREENS.enabler);
      setRoles(r);
      setIsAdmin(admin);
    } catch (e) {
      setPersona(null);
      setPersonaDef(null);
      setRoles([]);
      setIsAdmin(false);
    }
  }, []);

  useEffect(() => { syncFromSession(); }, [syncFromSession]);

  // Re-sync when localStorage changes
  useEffect(() => {
    const handleStorage = () => syncFromSession();
    window.addEventListener('storage', handleStorage);
    const interval = setInterval(syncFromSession, 500);
    return () => {
      window.removeEventListener('storage', handleStorage);
      clearInterval(interval);
    };
  }, [syncFromSession]);

  const canAccessScreen = useCallback((screenId) => {
    if (!screenId) return true;
    if (!persona) return true;  // no persona yet = show everything (pre-login state)
    if (isAdmin) return true;
    for (const role of roles) {
      const def = PERSONA_SCREENS[role];
      if (def && def.screens.includes(screenId)) return true;
    }
    return false;
  }, [persona, isAdmin, roles]);

  const canAccessFeature = useCallback((featureId) => {
    if (!persona) return true;
    if (isAdmin) return true;
    for (const role of roles) {
      const def = PERSONA_SCREENS[role];
      if (def && def.features.includes(featureId)) return true;
    }
    return false;
  }, [persona, isAdmin, roles]);

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

  const switchRole = useCallback((newRole) => {
    if (!roles.includes(newRole) && !isAdmin) return false;
    const def = PERSONA_SCREENS[newRole];
    if (!def) return false;
    setPersona(newRole);
    setPersonaDef(def);
    try {
      const stored = localStorage.getItem('saro_session');
      if (stored) {
        const session = JSON.parse(stored);
        session.persona = newRole;
        session.persona_name = def.label;
        session.persona_icon = def.icon;
        session.default_page = def.defaultPage;
        localStorage.setItem('saro_session', JSON.stringify(session));
      }
    } catch (e) {}
    return true;
  }, [roles, isAdmin]);

  return (
    <PersonaContext.Provider value={{
      persona, personaDef, roles, isAdmin,
      canAccessScreen, canAccessFeature, getAllowedScreens, switchRole,
      PERSONA_SCREENS, ADMIN_SCREENS,
    }}>
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
