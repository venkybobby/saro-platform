/**
 * SARO — Persona-Aware Navigation Sidebar
 * ==========================================
 * Only shows nav items the current persona can access.
 * Multi-role users see the union of all their roles' screens.
 * Includes role switcher for multi-role users.
 *
 * Drop this into your existing layout to replace the current nav.
 */

import { usePersona } from "../hooks/PersonaContext";

// ─── All possible nav items with screen IDs ───────────────────────
const ALL_NAV_ITEMS = [
  // Forecaster screens
  { id: "mvp1",            label: "Regulatory Forecast", icon: "📈", screen: "mvp1" },
  { id: "scenario",        label: "Scenario Modeler",    icon: "🔮", screen: "mvp1" },

  // Autopsier screens
  { id: "auditflow",       label: "Audit Flow",          icon: "🔍", screen: "auditflow" },
  { id: "audit-explorer",  label: "Audit DB Explorer",   icon: "🗄️", screen: "audit-explorer" },
  { id: "compliance-map",  label: "Compliance Map",       icon: "🗺️", screen: "compliance-map" },

  // Enabler screens
  { id: "mvp4",            label: "Controls & Policies",  icon: "⚙️", screen: "mvp4" },
  { id: "onboarding",      label: "Onboarding",           icon: "🚀", screen: "onboarding" },
  { id: "integrations",    label: "Integrations",         icon: "🔗", screen: "integrations" },
  { id: "training",        label: "Training Hub",         icon: "📚", screen: "training" },

  // Evangelist screens
  { id: "dashboard",       label: "Executive Dashboard",  icon: "🎯", screen: "dashboard" },
  { id: "ethics",          label: "Ethics & Trust",        icon: "⚖️", screen: "ethics" },
  { id: "reports",         label: "Reports",               icon: "📊", screen: "reports" },
  { id: "executive",       label: "Board Summary",         icon: "👔", screen: "executive" },

  // Admin-only
  { id: "admin",           label: "Admin Panel",           icon: "🛡️", screen: "admin",       adminOnly: true },
  { id: "provisioning",    label: "User Provisioning",     icon: "👥", screen: "provisioning", adminOnly: true },
];

export default function PersonaNav({ activePage, onNavigate }) {
  const {
    persona, personaDef, roles, isAdmin,
    canAccessScreen, switchRole,
    PERSONA_SCREENS, logout,
  } = usePersona();

  if (!persona) return null;

  // Filter nav items to only what this user can see
  const visibleItems = ALL_NAV_ITEMS.filter(item => {
    if (item.adminOnly && !isAdmin) return false;
    return canAccessScreen(item.screen);
  });

  // Group by screen for cleaner display
  const seen = new Set();
  const deduped = visibleItems.filter(item => {
    if (seen.has(item.id)) return false;
    seen.add(item.id);
    return true;
  });

  return (
    <div className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col h-screen">
      {/* Persona Header */}
      <div
        className="p-4 border-b border-gray-800"
        style={{ borderLeftColor: personaDef?.color, borderLeftWidth: 3 }}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xl">{personaDef?.icon}</span>
          <span
            className="font-semibold text-sm"
            style={{ color: personaDef?.color }}
          >
            {personaDef?.label}
          </span>
        </div>
        <p className="text-xs text-gray-500 leading-tight">
          {personaDef?.description}
        </p>
      </div>

      {/* Multi-Role Switcher */}
      {roles.length > 1 && (
        <div className="px-3 py-2 border-b border-gray-800/50">
          <p className="text-[10px] uppercase tracking-wider text-gray-600 mb-1.5">
            Switch Role
          </p>
          <div className="flex flex-wrap gap-1">
            {roles.map(role => {
              const def = PERSONA_SCREENS[role];
              if (!def) return null;
              const isActive = role === persona;
              return (
                <button
                  key={role}
                  onClick={() => {
                    switchRole(role);
                    onNavigate(def.defaultPage);
                  }}
                  className={`
                    text-xs px-2 py-0.5 rounded-full transition-all
                    ${isActive
                      ? "ring-1 ring-offset-1 ring-offset-gray-950"
                      : "opacity-50 hover:opacity-80"
                    }
                  `}
                  style={{
                    backgroundColor: isActive ? `${def.color}22` : "transparent",
                    color: def.color,
                    borderColor: def.color,
                    ringColor: def.color,
                  }}
                >
                  {def.icon} {def.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Nav Items */}
      <nav className="flex-1 overflow-y-auto py-2">
        {deduped.map(item => {
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                w-full text-left px-4 py-2.5 flex items-center gap-3
                text-sm transition-colors
                ${isActive
                  ? "bg-gray-800/80 text-white"
                  : "text-gray-400 hover:text-gray-200 hover:bg-gray-900/60"
                }
              `}
              style={isActive ? { borderLeft: `2px solid ${personaDef?.color}` } : { borderLeft: "2px solid transparent" }}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
              {item.adminOnly && (
                <span className="ml-auto text-[10px] bg-red-900/40 text-red-400 px-1.5 py-0.5 rounded">
                  ADMIN
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Persona Metrics Card */}
      {personaDef?.metrics && (
        <div className="px-3 py-3 border-t border-gray-800">
          <p className="text-[10px] uppercase tracking-wider text-gray-600 mb-2">
            Key Metrics
          </p>
          <div className="space-y-1.5">
            {personaDef.metrics.slice(0, 3).map(m => (
              <div key={m.key} className="flex justify-between items-center" title={m.tooltip}>
                <span className="text-xs text-gray-500">{m.label}</span>
                <span className="text-xs font-mono text-gray-300">{m.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logout */}
      <div className="p-3 border-t border-gray-800">
        <button
          onClick={logout}
          className="w-full text-left text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1.5 rounded hover:bg-gray-900/40"
        >
          ↩ Sign Out
        </button>
      </div>
    </div>
  );
}

export { ALL_NAV_ITEMS };
