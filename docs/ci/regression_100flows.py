#!/usr/bin/env python3
"""
SARO 100-Flow Nightly Regression Script (FR-TEST-01..03)

Runs 100 end-to-end flows covering:
  - 4 domains: finance, healthcare, hr, general
  - 4 policies: EU AI Act, NIST AI RMF, ISO 42001, FDA SaMD
  - 4 personas: forecaster, autopsier, enabler, evangelist
  - 3 input types: text, structured, nonstandard doc

Pass criteria (NFR-04):
  - Average mitigation rate >= 70%
  - Average latency <= 30s per flow
  - Error rate <= 5%

Usage:
  python regression_100flows.py --url https://backend.koyeb.app --flows 100
"""
import requests, json, time, random, argparse, sys, os
from datetime import datetime

GREEN  = "\033[92m"
CYAN   = "\033[96m"
AMBER  = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✓{RESET}  {msg}")
def info(msg):  print(f"  {CYAN}→{RESET}  {msg}")
def warn(msg):  print(f"  {AMBER}⚠{RESET}  {msg}")
def fail(msg):  print(f"  {RED}✗{RESET}  {msg}")

# ── Flow scenarios (mix of all spec scenarios) ─────────────────────────
DOMAINS   = ["finance", "healthcare", "hr", "general"]
POLICIES  = ["EU AI Act", "NIST AI RMF", "ISO 42001", "FDA SaMD"]
PERSONAS  = ["forecaster", "autopsier", "enabler", "evangelist"]
SCENARIOS = [
    # Finance — critical
    {"model_name":"CreditScorer-v2","domain":"finance","policy":"EU AI Act","output_text":"Loan denied. Gender and race used as direct features. No adverse action reason. No human oversight."},
    # Finance — clean
    {"model_name":"CreditAssist-v1","domain":"finance","policy":"EU AI Act","output_text":"Loan approved. Model uses income, debt ratio. Adverse action documented. Human review complete. Audit trail: CR-20260301."},
    # Healthcare — critical
    {"model_name":"DiagAI-v1","domain":"healthcare","policy":"FDA SaMD","output_text":"Cancer probability 64%. Trained on 200 patients. No physician override. No documentation."},
    # Healthcare — warn
    {"model_name":"DiagAI-v2","domain":"healthcare","policy":"FDA SaMD","output_text":"Stroke risk: 41%. Model validated on 1,200 patients. Physician review available. Partial documentation."},
    # HR — clean
    {"model_name":"HRScreen-v3","domain":"hr","policy":"NIST AI RMF","output_text":"Candidate ranked #3. Disparate impact: 0.87 (above 4/5). Human review: YES. Audit trail: HR-20260301."},
    # General structured
    {"model_name":"GenModel","domain":"general","policy":"ISO 42001","output_data":{"bias_score":0.22,"accuracy":0.81,"transparency_score":0.55,"human_oversight":False}},
    # Finance structured — bad
    {"model_name":"RiskModel","domain":"finance","policy":"EU AI Act","output_data":{"bias_score":0.35,"accuracy":0.70,"transparency_score":0.38,"human_oversight":False}},
    # Healthcare structured — good
    {"model_name":"ClinicalAI","domain":"healthcare","policy":"FDA SaMD","output_data":{"bias_score":0.05,"accuracy":0.93,"transparency_score":0.82,"human_oversight":True}},
]

NONSTANDARD_DOCS = [
    {"title":"Internal AI Policy","jurisdiction":"EU","content":"All AI systems must have documented bias testing, transparency obligations, and human oversight. Prohibited uses include emotion recognition. High-risk systems need full documentation."},
    {"title":"Vendor AI Contract","jurisdiction":"US","content":"AI models must achieve 85% accuracy. Facial recognition is prohibited. Customers may audit model behaviour. Disparate impact testing required."},
]


def run_flow(url: str, flow_idx: int, scenario: dict, endpoint: str) -> dict:
    start = time.time()
    try:
        if endpoint == "agent":
            resp = requests.post(f"{url}/api/v1/agent/run", json=scenario, timeout=45)
        elif endpoint == "model_upload":
            resp = requests.post(f"{url}/api/v1/model-output/upload", json=scenario, timeout=45)
        elif endpoint == "nonstandard":
            resp = requests.post(f"{url}/api/v1/agent/ingest-nonstandard", json=scenario, timeout=45)
        elif endpoint == "gateway":
            resp = requests.post(f"{url}/api/v1/gateway/submit", json=scenario, timeout=45)
        elif endpoint == "auth_magic":
            resp = requests.post(f"{url}/api/v1/auth/magic-link", json=scenario, timeout=15)
        elif endpoint == "try_free":
            resp = requests.post(f"{url}/api/v1/auth/try-free", json=scenario, timeout=15)
        elif endpoint == "policy_chat":
            resp = requests.post(f"{url}/api/v1/policy-chat/ask", json=scenario, timeout=15)
        else:
            resp = requests.get(f"{url}/health", timeout=10)

        latency_ms = (time.time() - start) * 1000
        data = resp.json()

        # Extract compliance/mitigation score
        score = None
        if "summary" in data:
            s = data["summary"]
            score = s.get("compliance_score") or s.get("pass_rate", 0) / 100
        elif "compliance_score" in data:
            score = data["compliance_score"]
        elif "overall_risk_score" in data:
            score = 1.0 - data["overall_risk_score"]  # Invert risk to get mitigation

        return {
            "flow_idx":   flow_idx,
            "endpoint":   endpoint,
            "status_code": resp.status_code,
            "success":    resp.status_code < 400,
            "latency_ms": latency_ms,
            "score":      score,
            "model_name": scenario.get("model_name", "n/a"),
            "domain":     scenario.get("domain", "n/a"),
        }

    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "flow_idx": flow_idx, "endpoint": endpoint,
            "status_code": 0, "success": False,
            "latency_ms": latency_ms, "score": None,
            "error": str(e)[:200],
            "model_name": scenario.get("model_name","n/a"),
            "domain": scenario.get("domain","n/a"),
        }


def build_100_flows() -> list[tuple[str,dict]]:
    """Build 100 flows covering all scenarios and endpoints."""
    flows = []

    # 30 agent/run flows (full pipeline)
    for i in range(30):
        s = SCENARIOS[i % len(SCENARIOS)].copy()
        s["domain"]  = DOMAINS[i % 4]
        s["policy"]  = POLICIES[i % 4]
        s["persona"] = PERSONAS[i % 4]
        flows.append(("agent", s))

    # 20 model-output/upload flows
    for i in range(20):
        s = SCENARIOS[i % len(SCENARIOS)].copy()
        flows.append(("model_upload", s))

    # 10 gateway flows
    for i in range(10):
        s = SCENARIOS[i % len(SCENARIOS)].copy()
        flows.append(("gateway", s))

    # 10 nonstandard doc flows
    for i in range(10):
        flows.append(("nonstandard", NONSTANDARD_DOCS[i % len(NONSTANDARD_DOCS)].copy()))

    # 10 magic link auth flows
    for i in range(10):
        flows.append(("auth_magic", {"email": f"test{i}@bank.com", "persona": PERSONAS[i%4]}))

    # 5 try-free flows
    for i in range(5):
        flows.append(("try_free", {"email": f"trial{i}@tech.co", "persona": PERSONAS[i%4]}))

    # 10 policy chat flows
    questions = [
        "What does EU AI Act Article 10 require?",
        "How does NIST MAP 2.3 define bias risk?",
        "What accuracy does FDA SaMD require?",
        "Which AI uses are prohibited under Article 5?",
        "What is ISO 42001 A.8.4?",
    ]
    for i in range(10):
        flows.append(("policy_chat", {"query": questions[i%len(questions)], "session_id": f"test-{i}"}))

    # 5 health check flows
    for i in range(5):
        flows.append(("health", {}))

    random.shuffle(flows)
    return flows[:100]


def main():
    parser = argparse.ArgumentParser(description="SARO 100-flow nightly regression")
    parser.add_argument("--url",                  default="http://localhost:8000")
    parser.add_argument("--flows",      type=int, default=100)
    parser.add_argument("--mitigation-threshold", type=float, default=70.0)
    parser.add_argument("--latency-threshold",    type=float, default=30000.0)
    parser.add_argument("--error-threshold",      type=float, default=5.0)
    args = parser.parse_args()

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}SARO Nightly Regression — {args.flows} Flows{RESET}")
    print(f"Backend:  {args.url}")
    print(f"Started:  {datetime.utcnow().isoformat()}Z")
    print(f"Targets:  mitigation≥{args.mitigation_threshold}% · latency≤{args.latency_threshold}ms · errors≤{args.error_threshold}%")
    print(f"{'='*60}\n")

    # Health check first
    try:
        r = requests.get(f"{args.url}/health", timeout=10)
        ok(f"Backend reachable — {r.status_code}")
    except Exception as e:
        fail(f"Backend unreachable: {e}")
        sys.exit(1)

    flows = build_100_flows()[:args.flows]
    results = []
    passed = failed = 0

    for i, (endpoint, scenario) in enumerate(flows):
        r = run_flow(args.url, i+1, scenario, endpoint)
        results.append(r)
        if r["success"]:
            passed += 1
            if (i+1) % 10 == 0:
                score_str = f"score={r['score']:.2f}" if r['score'] is not None else ""
                ok(f"Flow {i+1:03d}/{args.flows} — {endpoint:15s} {r['latency_ms']:.0f}ms {score_str}")
        else:
            failed += 1
            warn(f"Flow {i+1:03d}/{args.flows} — {endpoint:15s} FAILED {r.get('error','HTTP '+str(r['status_code']))[:60]}")

    # ── Results analysis ───────────────────────────────────────────────
    total         = len(results)
    error_rate    = (failed / total) * 100
    avg_latency   = sum(r["latency_ms"] for r in results) / total
    scored        = [r["score"] for r in results if r["score"] is not None]
    avg_score     = (sum(scored) / len(scored) * 100) if scored else 0

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}RESULTS SUMMARY{RESET}")
    print(f"{'='*60}")
    print(f"Total flows:      {total}")
    print(f"Passed:           {BOLD}{GREEN}{passed}{RESET} ({100-error_rate:.1f}%)")
    print(f"Failed:           {BOLD}{RED}{failed}{RESET} ({error_rate:.1f}%)")
    print(f"Avg latency:      {avg_latency:.0f}ms")
    print(f"Avg mitigation:   {avg_score:.1f}%")

    # ── Pass/fail thresholds ───────────────────────────────────────────
    violations = []
    if avg_score < args.mitigation_threshold:
        violations.append(f"Mitigation {avg_score:.1f}% < threshold {args.mitigation_threshold}%")
    if avg_latency > args.latency_threshold:
        violations.append(f"Latency {avg_latency:.0f}ms > threshold {args.latency_threshold:.0f}ms")
    if error_rate > args.error_threshold:
        violations.append(f"Error rate {error_rate:.1f}% > threshold {args.error_threshold}%")

    # ── Write report JSON ──────────────────────────────────────────────
    report = {
        "run_at":          datetime.utcnow().isoformat(),
        "backend_url":     args.url,
        "total_flows":     total,
        "passed":          passed,
        "failed":          failed,
        "error_rate_pct":  round(error_rate, 2),
        "avg_latency_ms":  round(avg_latency, 1),
        "avg_mitigation_pct": round(avg_score, 1),
        "violations":      violations,
        "passed_overall":  len(violations) == 0,
        "flows":           results,
    }
    with open("regression_report.json", "w") as f:
        json.dump(report, f, indent=2)
    info("Report saved to regression_report.json")

    if violations:
        print(f"\n{BOLD}{RED}REGRESSION FAILED — {len(violations)} threshold violation(s):{RESET}")
        for v in violations: fail(v)
        sys.exit(1)
    else:
        print(f"\n{BOLD}{GREEN}ALL REGRESSION CHECKS PASSED ✓{RESET}")
        print(f"  Mitigation: {avg_score:.1f}% ≥ {args.mitigation_threshold}% ✓")
        print(f"  Latency:    {avg_latency:.0f}ms ≤ {args.latency_threshold:.0f}ms ✓")
        print(f"  Errors:     {error_rate:.1f}% ≤ {args.error_threshold}% ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
