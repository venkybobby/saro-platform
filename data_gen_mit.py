"""
data_gen_mit.py — MIT AI Risk Repository Test Case Generator
=============================================================
Generates 200 structured test cases from the MIT AI Risk Repository.

Usage:
  python data_gen_mit.py [--excel path/to/AI_Risk_Repository.xlsx]

If the Excel file is not available, falls back to synthetic generation
from the embedded MIT domain taxonomy (7 domains, 24 subdomains).

Output: test_data_mit_200.json (loaded by audit_engine during test runs)

MIT AI Risk Repository: https://airisks.mit.edu
Reference: "The AI Risk Repository" — MIT FutureTech, 2024
"""

import json
import random
import argparse
from pathlib import Path

# ── Embedded taxonomy — mirrors backend/app/api/audit_engine.py MIT_DOMAIN_TAXONOMY ──
MIT_DOMAIN_TAXONOMY = {
    "Discrimination & Toxicity": {
        "subdomains": [
            "Unfair discrimination in high-stakes decisions",
            "Exposure to toxic or harmful content",
            "Unequal performance across demographic groups",
        ],
        "causal_entities": ["Developer", "Deployer"],
        "causal_intent":  ["Unintentional"],
        "causal_timing":  ["Pre-deployment", "Post-deployment"],
        "example_risks": [
            "Loan denial rate 22% higher for protected group due to proxy features",
            "Resume ranking model exhibits gender bias (disparate impact ratio 0.78)",
            "Facial recognition accuracy drops 18% for darker skin tones",
            "Sentiment classifier assigns negative scores to minority dialects",
            "Credit scoring model uses zip code as race proxy",
        ],
        "nist_controls": ["GOVERN-1.6", "MAP-2.3", "MEASURE-2.3"],
        "mit_mitigations": ["Technical", "Governance"],
    },
    "Privacy & Security": {
        "subdomains": [
            "Unauthorised personal data collection",
            "Model inversion / membership inference attacks",
            "Cybersecurity vulnerabilities in AI systems",
        ],
        "causal_entities": ["Deployer", "Malicious Actor"],
        "causal_intent":  ["Intentional", "Unintentional"],
        "causal_timing":  ["Post-deployment"],
        "example_risks": [
            "LLM memorises and reproduces training PII (SSN, names, addresses)",
            "Model output leaks confidential patient health records",
            "Membership inference attack reveals sensitive training data",
            "Adversarial query extracts embedding weights from production model",
            "AI assistant stores conversation history without consent",
        ],
        "nist_controls": ["GOVERN-1.7", "MAP-1.6", "MEASURE-2.6", "MEASURE-2.7"],
        "mit_mitigations": ["Technical", "Governance"],
    },
    "Misinformation": {
        "subdomains": [
            "Generation of false or misleading information",
            "Hallucination and groundedness failures",
            "AI-enabled manipulation at scale",
        ],
        "causal_entities": ["Developer", "User", "Malicious Actor"],
        "causal_intent":  ["Unintentional", "Intentional"],
        "causal_timing":  ["Post-deployment"],
        "example_risks": [
            "Medical chatbot provides incorrect drug dosage (hallucination)",
            "LLM fabricates legal citations that don't exist",
            "AI news summariser omits critical context, distorting meaning",
            "Deepfake generator used to spread disinformation about public figures",
            "RAG system retrieves stale data, producing outdated compliance advice",
        ],
        "nist_controls": ["MEASURE-2.1", "MEASURE-2.4", "MEASURE-3.1"],
        "mit_mitigations": ["Technical", "Transparency"],
    },
    "Malicious Use": {
        "subdomains": [
            "AI-assisted cyberattack facilitation",
            "Fraud, social engineering and scams",
            "Adversarial exploits and jailbreaks",
        ],
        "causal_entities": ["Malicious Actor", "Deployer"],
        "causal_intent":  ["Intentional"],
        "causal_timing":  ["Post-deployment"],
        "example_risks": [
            "LLM jailbreak bypasses safety filters to produce harmful content",
            "AI-generated phishing emails with 94% open rate vs 23% baseline",
            "Code generation model produces functional malware on request",
            "Voice cloning used to impersonate executives for wire fraud",
            "Adversarial perturbation fools autonomous vehicle object detection",
        ],
        "nist_controls": ["MEASURE-2.2", "MANAGE-4.2"],
        "mit_mitigations": ["Technical", "Operational"],
    },
    "Human-Computer Interaction": {
        "subdomains": [
            "Overreliance and automation bias",
            "Inappropriate anthropomorphism",
            "Inadequate human oversight mechanisms",
        ],
        "causal_entities": ["Developer", "User"],
        "causal_intent":  ["Unintentional"],
        "causal_timing":  ["Post-deployment"],
        "example_risks": [
            "Clinicians override AI alerts less than 5% of the time, ignoring valid concerns",
            "Users trust AI medical diagnosis without seeking human review",
            "Lack of explainability prevents appeals for automated credit denial",
            "AI customer service presents as human, eroding trust when discovered",
            "Automated decision system provides no human escalation path",
        ],
        "nist_controls": ["GOVERN-3.2", "MEASURE-2.4", "MEASURE-2.8", "MANAGE-1.3"],
        "mit_mitigations": ["Governance", "Transparency"],
    },
    "Socioeconomic & Environmental": {
        "subdomains": [
            "Labour displacement and economic disruption",
            "Exacerbation of economic inequality",
            "Environmental and resource costs",
        ],
        "causal_entities": ["Developer", "Deployer", "Researcher"],
        "causal_intent":  ["Unintentional"],
        "causal_timing":  ["Post-deployment"],
        "example_risks": [
            "AI-driven automation displaces 40% of data entry workforce with no retraining",
            "AI hiring tool filters out candidates from lower-income zip codes",
            "LLM training run emits equivalent of 5 transatlantic flights in CO2",
            "Algorithm-driven lending concentrates credit access in affluent areas",
            "AI regulatory compliance burden disproportionately impacts small firms",
        ],
        "nist_controls": ["GOVERN-1.1", "GOVERN-1.7", "MAP-3.2"],
        "mit_mitigations": ["Governance", "Operational"],
    },
    "AI System Safety": {
        "subdomains": [
            "Unexpected, erratic or harmful AI behaviour",
            "Lack of robustness and distributional shift",
            "System failures with cascading consequences",
        ],
        "causal_entities": ["Developer", "Researcher"],
        "causal_intent":  ["Unintentional"],
        "causal_timing":  ["Pre-deployment", "Post-deployment"],
        "example_risks": [
            "Model distribution shift post-deployment causes 30% accuracy degradation",
            "Autonomous agent enters reward hacking loop, consuming excessive resources",
            "Missing post-market monitoring — no alert when fraud detection F1 drops to 0.51",
            "AI system lacks human override — operator cannot stop automated decisions",
            "Cascading failure: AI recommendations trigger flash crash in equity markets",
        ],
        "nist_controls": ["MAP-1.6", "MANAGE-1.1", "MANAGE-2.2", "MANAGE-2.3"],
        "mit_mitigations": ["Technical", "Operational"],
    },
}

SEVERITY_BY_DOMAIN = {
    "Discrimination & Toxicity":  ["high",     "critical", "high",    "medium",  "critical"],
    "Privacy & Security":         ["critical",  "high",     "critical", "high",   "high"],
    "Misinformation":             ["high",      "critical", "medium",  "high",    "medium"],
    "Malicious Use":              ["critical",  "critical", "critical", "high",   "critical"],
    "Human-Computer Interaction": ["medium",    "high",     "high",    "medium",  "high"],
    "Socioeconomic & Environmental": ["medium", "high",     "low",     "high",    "medium"],
    "AI System Safety":           ["high",      "medium",   "high",    "critical","critical"],
}

DOMAIN_MITIGATION_HINT = {
    "Discrimination & Toxicity":  "Apply equalized odds post-processing; rebalance training data; conduct fairness audits quarterly.",
    "Privacy & Security":         "Integrate Presidio NER; enforce differential privacy; conduct model extraction threat modelling.",
    "Misinformation":             "Implement RAG grounding checks (Ragas faithfulness ≥ 0.9); add citations; enable human review for high-stakes outputs.",
    "Malicious Use":              "Deploy PyRIT adversarial testing suite; implement content filtering; monitor for jailbreak patterns.",
    "Human-Computer Interaction": "Add SHAP/LIME explainability; implement mandatory human review for critical decisions; provide appeal mechanism.",
    "Socioeconomic & Environmental": "Conduct societal impact assessment; establish worker transition support; measure and offset carbon footprint.",
    "AI System Safety":           "Implement continuous monitoring (Evidently AI / Arize); enforce human kill-switch; document distributional assumptions.",
}


def load_from_excel(excel_path: str) -> list:
    """
    Parse the MIT AI Risk Repository Excel file.
    Expected columns: Ev_ID, Domain, Sub-domain, Entity, Intent, Timing, Description
    """
    try:
        import pandas as pd
    except ImportError:
        print("pandas not installed. Run: pip install pandas openpyxl")
        return []

    try:
        df = pd.read_excel(excel_path, sheet_name="AI Risk Database v3")
    except Exception as e:
        print(f"Could not read Excel ({e}). Falling back to synthetic generation.")
        return []

    cases = []
    for _, row in df.iterrows():
        domain = row.get("Domain")
        desc   = row.get("Description")
        if pd.isna(domain) or pd.isna(desc):
            continue
        domain_str = str(domain).strip()
        cases.append({
            "risk_id":          str(row.get("Ev_ID", f"MIT-{len(cases)+1:04d}")),
            "domain":           domain_str,
            "sub_domain":       str(row.get("Sub-domain", "")).strip() or None,
            "causal": {
                "entity":  str(row.get("Entity",  "")).strip() or "Developer",
                "intent":  str(row.get("Intent",  "")).strip() or "Unintentional",
                "timing":  str(row.get("Timing",  "")).strip() or "Post-deployment",
            },
            "description":      str(desc)[:800],
            "severity":         "high",  # Excel doesn't have this; default to high
            "mitigation_hint":  DOMAIN_MITIGATION_HINT.get(domain_str, "Review SARO remediation plan."),
            "nist_controls":    MIT_DOMAIN_TAXONOMY.get(domain_str, {}).get("nist_controls", []),
            "source":           "MIT AI Risk Repository v3 (2025)",
            "expected_metrics": {
                "bias_disparity": 0.18 if "Discrimination" in domain_str else 0.05,
                "pii_leak_rate":  2    if "Privacy"         in domain_str else 0,
            },
        })
    return cases


def generate_synthetic(target: int = 200) -> list:
    """
    Generate synthetic test cases from embedded taxonomy.
    Produces realistic, structurally valid test data for CI and demo purposes.
    """
    random.seed(42)  # deterministic for reproducibility
    cases = []
    counter = 1
    domains = list(MIT_DOMAIN_TAXONOMY.keys())

    # Round-robin through domains to ensure coverage across all 7
    per_domain = target // len(domains)
    extras = target % len(domains)

    for di, domain in enumerate(domains):
        cfg = MIT_DOMAIN_TAXONOMY[domain]
        n_cases = per_domain + (1 if di < extras else 0)

        for i in range(n_cases):
            subdomain = random.choice(cfg["subdomains"])
            entity    = random.choice(cfg["causal_entities"])
            intent    = random.choice(cfg["causal_intent"])
            timing    = random.choice(cfg["causal_timing"])
            risk_desc = random.choice(cfg["example_risks"])
            sev_list  = SEVERITY_BY_DOMAIN.get(domain, ["high", "medium"])
            severity  = sev_list[i % len(sev_list)]

            cases.append({
                "risk_id":         f"MIT-SYN-{counter:04d}",
                "domain":          domain,
                "sub_domain":      subdomain,
                "causal": {
                    "entity":  entity,
                    "intent":  intent,
                    "timing":  timing,
                },
                "description":     risk_desc,
                "severity":        severity,
                "mitigation_hint": DOMAIN_MITIGATION_HINT[domain],
                "nist_controls":   cfg["nist_controls"],
                "mit_mitigations": cfg["mit_mitigations"],
                "source":          "SARO synthetic — based on MIT AI Risk Repository taxonomy",
                "expected_metrics": {
                    "bias_disparity": 0.18 if "Discrimination" in domain else 0.05,
                    "pii_leak_rate":  2    if "Privacy"         in domain else 0,
                },
            })
            counter += 1

    random.shuffle(cases)
    return cases[:target]


def main():
    parser = argparse.ArgumentParser(description="Generate MIT AI Risk test cases")
    parser.add_argument("--excel", type=str, default=None,
                        help="Path to MIT AI Risk Repository Excel file")
    parser.add_argument("--output", type=str, default="test_data_mit_200.json",
                        help="Output JSON path")
    parser.add_argument("--count", type=int, default=200,
                        help="Number of test cases to generate")
    args = parser.parse_args()

    cases = []

    # 1. Try Excel first
    if args.excel and Path(args.excel).exists():
        print(f"Loading from Excel: {args.excel}")
        cases = load_from_excel(args.excel)
        print(f"  Loaded {len(cases)} cases from Excel")
        if len(cases) > args.count:
            cases = cases[:args.count]

    # 2. Supplement with synthetic if needed
    if len(cases) < args.count:
        need = args.count - len(cases)
        print(f"Generating {need} synthetic cases from embedded taxonomy...")
        synthetic = generate_synthetic(need)
        cases.extend(synthetic)

    print(f"\nTotal test cases: {len(cases)}")
    for domain in MIT_DOMAIN_TAXONOMY:
        count = sum(1 for c in cases if c["domain"] == domain)
        print(f"  {domain}: {count}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(cases, f, indent=2)

    print(f"\n✅ Generated {len(cases)} MIT test cases → {output_path}")
    return cases


if __name__ == "__main__":
    main()
