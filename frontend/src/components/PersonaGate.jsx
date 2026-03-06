/**
 * SARO — Persona Gate Components
 * ================================
 * Drop these around any screen/feature to enforce persona restrictions.
 *
 * Usage:
 *   <ScreenGate screen="auditflow">
 *     <AuditFlow />          ← only visible to autopsier
 *   </ScreenGate>
 *
 *   <FeatureGate feature="remediation">
 *     <RemediationPanel />   ← only visible to enabler
 *   </FeatureGate>
 */

import { usePersona } from "../hooks/PersonaContext";

// ─── Gate a full screen by screen ID ──────────────────────────────
export function ScreenGate({ screen, children, fallback = null }) {
  const { canAccessScreen, persona, loading } = usePersona();

  if (loading) return null;
  if (!persona) return fallback;
  if (!canAccessScreen(screen)) {
    return fallback || <AccessDenied type="screen" name={screen} />;
  }
  return children;
}

// ─── Gate a feature within a screen ───────────────────────────────
export function FeatureGate({ feature, children, fallback = null }) {
  const { canAccessFeature, persona, loading } = usePersona();

  if (loading) return null;
  if (!persona) return fallback;
  if (!canAccessFeature(feature)) {
    return fallback; // silently hide features (don't show denied message)
  }
  return children;
}

// ─── Gate for admin-only content ──────────────────────────────────
export function AdminGate({ children, fallback = null }) {
  const { isAdmin, loading } = usePersona();

  if (loading) return null;
  if (!isAdmin) return fallback || <AccessDenied type="admin" name="Admin Panel" />;
  return children;
}

// ─── Access Denied placeholder ────────────────────────────────────
function AccessDenied({ type, name }) {
  const { personaDef } = usePersona();
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center max-w-md p-8 rounded-2xl bg-gray-900/60 border border-gray-700/50">
        <div className="text-5xl mb-4">🔒</div>
        <h3 className="text-lg font-semibold text-gray-200 mb-2">
          Access Restricted
        </h3>
        <p className="text-sm text-gray-400 mb-4">
          The <span className="font-medium text-white">{name}</span> {type} is not
          available for the{" "}
          <span
            className="font-medium"
            style={{ color: personaDef?.color || "#999" }}
          >
            {personaDef?.icon} {personaDef?.label}
          </span>{" "}
          persona.
        </p>
        <p className="text-xs text-gray-500">
          Contact your admin to update your role assignment.
        </p>
      </div>
    </div>
  );
}
