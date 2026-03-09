/**
 * SARO — Persona Login Screen
 * ==============================
 * Replaces the plain magic-link flow with persona-aware onboarding.
 * Shows the 4 personas with descriptions; user picks one + enters email.
 */

import { useState } from "react";
import { usePersona, PERSONA_SCREENS } from "../hooks/PersonaContext";

export default function PersonaLogin() {
  const { login, loading, error } = usePersona();
  const [email, setEmail] = useState("");
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [step, setStep] = useState("persona"); // persona → email → done

  const personas = Object.entries(PERSONA_SCREENS);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !selectedPersona) return;
    const result = await login(email, selectedPersona);
    if (result) setStep("done");
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-white tracking-tight mb-2">
            SARO
          </h1>
          <p className="text-gray-400 text-sm">
            AI Regulatory Intelligence Platform
          </p>
        </div>

        {step === "persona" && (
          <>
            <p className="text-center text-gray-300 text-sm mb-6">
              Select your role to get a tailored experience
            </p>
            <div className="grid grid-cols-2 gap-4 mb-8">
              {personas.map(([id, def]) => (
                <button
                  key={id}
                  onClick={() => {
                    setSelectedPersona(id);
                    setStep("email");
                  }}
                  className={`
                    p-5 rounded-xl border text-left transition-all
                    hover:scale-[1.02] active:scale-[0.98]
                    ${selectedPersona === id
                      ? "border-opacity-100 bg-opacity-20"
                      : "border-gray-700/50 bg-gray-900/40 hover:border-gray-600"
                    }
                  `}
                  style={
                    selectedPersona === id
                      ? { borderColor: def.color, backgroundColor: `${def.color}15` }
                      : {}
                  }
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{def.icon}</span>
                    <span
                      className="font-semibold"
                      style={{ color: def.color }}
                    >
                      {def.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {def.description}
                  </p>
                </button>
              ))}
            </div>
          </>
        )}

        {step === "email" && (
          <form onSubmit={handleSubmit} className="max-w-sm mx-auto">
            {/* Selected persona badge */}
            <div className="flex items-center justify-center gap-2 mb-6">
              <span className="text-lg">{PERSONA_SCREENS[selectedPersona]?.icon}</span>
              <span
                className="font-medium text-sm"
                style={{ color: PERSONA_SCREENS[selectedPersona]?.color }}
              >
                {PERSONA_SCREENS[selectedPersona]?.label}
              </span>
              <button
                type="button"
                onClick={() => setStep("persona")}
                className="text-xs text-gray-500 hover:text-gray-300 ml-2"
              >
                (change)
              </button>
            </div>

            <label className="block text-sm text-gray-400 mb-2">
              Email address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white
                         placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50
                         focus:border-cyan-500 mb-4 text-sm"
            />

            <button
              type="submit"
              disabled={loading || !email}
              className="w-full py-3 rounded-lg font-medium text-sm text-white
                         transition-all disabled:opacity-50"
              style={{
                backgroundColor: PERSONA_SCREENS[selectedPersona]?.color || "#06b6d4",
              }}
            >
              {loading ? "Authenticating..." : "Continue with Magic Link"}
            </button>

            {error && (
              <p className="text-red-400 text-xs mt-3 text-center">{error}</p>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
