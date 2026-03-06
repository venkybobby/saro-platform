/**
 * SARO — Persona Metrics Dashboard Card
 * ========================================
 * Shows the persona's KPI metrics with tooltips (FR-FOR-03, FR-AUT-03, etc.)
 * Clean card layout, max 5 metrics, contextual colors.
 */

import { useState } from "react";
import { usePersona } from "../hooks/PersonaContext";

export default function PersonaMetricsCard() {
  const { personaDef } = usePersona();
  const [hoveredMetric, setHoveredMetric] = useState(null);

  if (!personaDef?.metrics) return null;

  return (
    <div className="bg-gray-900/60 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">{personaDef.icon}</span>
        <h3
          className="text-sm font-semibold"
          style={{ color: personaDef.color }}
        >
          {personaDef.label} Metrics
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {personaDef.metrics.map((m) => {
          const isHovered = hoveredMetric === m.key;
          return (
            <div
              key={m.key}
              className="relative p-3 rounded-lg bg-gray-800/50 border border-gray-700/30
                         hover:border-gray-600/50 transition-all cursor-default"
              onMouseEnter={() => setHoveredMetric(m.key)}
              onMouseLeave={() => setHoveredMetric(null)}
            >
              <p className="text-[11px] text-gray-500 mb-1">{m.label}</p>
              <p className="text-lg font-semibold text-white">{m.value}</p>
              <p className="text-[10px] text-gray-600 mt-0.5">
                Target: {m.target}
              </p>

              {/* Tooltip on hover */}
              {isHovered && m.tooltip && (
                <div className="absolute bottom-full left-0 mb-2 z-50 w-56
                                bg-gray-800 border border-gray-700 rounded-lg
                                px-3 py-2 shadow-xl pointer-events-none">
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {m.tooltip}
                  </p>
                  <div className="absolute top-full left-4 w-2 h-2
                                  bg-gray-800 border-r border-b border-gray-700
                                  transform rotate-45 -mt-1" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
