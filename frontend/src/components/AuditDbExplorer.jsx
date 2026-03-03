// AuditDbExplorer.jsx -- SARO v8.0 DB-backed audit explorer
import { useState, useEffect, useCallback } from "react";

const RISK_COLOURS = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

function ScoreBar({ score }) {
  const pct = Math.round((score || 0) * 100);
  const col = pct >= 80 ? "#22c55e" : pct >= 60 ? "#f59e0b" : "#ef4444";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded h-2">
        <div style={{ width: `${pct}%`, backgroundColor: col }} className="h-2 rounded" />
      </div>
      <span className="text-xs font-mono">{pct}%</span>
    </div>
  );
}

export default function AuditDbExplorer() {
  const [audits, setAudits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(null);
  const PAGE = 10;

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const r = await fetch("/api/audits?limit=200");
      const d = await r.json();
      setAudits(d.audits || []);
      setSource(d.source || "");
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const pages = Math.ceil(audits.length / PAGE);
  const slice = audits.slice((page - 1) * PAGE, page * PAGE);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Audit DB Explorer</h2>
          <p className="text-xs text-gray-500 mt-1">
            {audits.length} records &bull; source: <code className="bg-gray-100 px-1 rounded">{source || "?"}</code>
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="px-4 py-2 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700 disabled:opacity-50">
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>{["Audit ID","Type","Score","Risk","Created"].map(h => (
              <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
            ))}</tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {slice.length === 0
              ? <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">{loading ? "Loading..." : "No records."}</td></tr>
              : slice.map(a => {
                  const rl = (a.risk_level || "medium").toLowerCase();
                  return (
                    <tr key={a.audit_id} className="hover:bg-indigo-50 cursor-pointer" onClick={() => setSelected(a)}>
                      <td className="px-4 py-3 font-mono text-xs text-indigo-700">{a.audit_id}</td>
                      <td className="px-4 py-3 text-gray-700">{a.audit_type || "--"}</td>
                      <td className="px-4 py-3 w-32"><ScoreBar score={a.score} /></td>
                      <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded-full font-medium capitalize ${RISK_COLOURS[rl] || ""}`}>{rl}</span></td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{a.created_at ? new Date(a.created_at).toLocaleString() : "--"}</td>
                    </tr>
                  );
                })
            }
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="px-3 py-1.5 text-sm rounded border disabled:opacity-40">Prev</button>
          <span className="text-sm text-gray-600">Page {page}/{pages}</span>
          <button onClick={() => setPage(p => Math.min(pages,p+1))} disabled={page===pages} className="px-3 py-1.5 text-sm rounded border disabled:opacity-40">Next</button>
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/40 flex justify-end z-50" onClick={() => setSelected(null)}>
          <div className="w-full max-w-md bg-white h-full overflow-y-auto p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between mb-4">
              <h3 className="text-lg font-semibold">Audit Detail</h3>
              <button onClick={() => setSelected(null)} className="text-gray-400 text-xl">&times;</button>
            </div>
            <dl className="space-y-3 text-sm">
              {Object.entries(selected).map(([k,v]) => (
                <div key={k} className="grid grid-cols-3 gap-1">
                  <dt className="font-medium text-gray-500 capitalize">{k.replace(/_/g," ")}</dt>
                  <dd className="col-span-2 font-mono text-xs break-all">{typeof v==="object"?JSON.stringify(v):String(v)}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}
