"""
SARO Platform — Demo Data Seeder
Populates all 4 MVP modules with realistic data for live demos.
Run: python seed_demo.py --url https://your-railway-url.up.railway.app
"""
import asyncio
import httpx
import argparse
import random
import sys
from datetime import datetime

# ── Colors ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
CYAN   = "\033[96m"
AMBER  = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")
def warn(msg): print(f"  {AMBER}!{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")

# ── Demo Documents (MVP1) ─────────────────────────────────────────────
DEMO_DOCUMENTS = [
    {
        "title": "EU AI Act — Article 9: Risk Management System",
        "jurisdiction": "EU",
        "doc_type": "regulation",
        "content": """Article 9 of the EU AI Act requires providers of high-risk AI systems to establish, implement, 
document and maintain a risk management system. This system shall consist of a continuous iterative process 
run throughout the entire lifecycle of a high-risk AI system. The risk management system shall identify and 
analyse known and reasonably foreseeable risks that the high-risk AI system can pose to health, safety or 
fundamental rights. It shall estimate and evaluate the risks that may emerge when the high-risk AI system 
is used in accordance with its intended purpose and under conditions of reasonably foreseeable misuse. 
Bias detection, transparency requirements, and data quality standards must all meet the Article 10 criteria 
for training datasets. Surveillance systems and biometric identification AI face unacceptable risk classification 
under Article 5. Safety requirements for healthcare AI must include human oversight mechanisms."""
    },
    {
        "title": "NIST AI Risk Management Framework 2.0 — Core Functions",
        "jurisdiction": "US",
        "doc_type": "standard",
        "content": """The NIST AI RMF 2.0 introduces four core functions: GOVERN, MAP, MEASURE, and MANAGE. 
Organizations deploying AI systems must establish governance structures that promote accountability and 
transparency in AI decision-making. The framework addresses bias and fairness through systematic measurement 
and evaluation protocols. High-risk AI applications in financial services, healthcare, and human resources 
require enhanced risk assessment procedures. The framework emphasizes the importance of explainability 
and human oversight for automated decision systems. Data quality standards must ensure representativeness 
and accuracy across all training datasets. Safety requirements include continuous monitoring and incident 
response protocols for AI systems in critical infrastructure."""
    },
    {
        "title": "MAS Technology Risk Guidelines — AI/ML Model Risk",
        "jurisdiction": "SG",
        "doc_type": "guideline",
        "content": """The Monetary Authority of Singapore's Technology Risk Guidelines establish requirements for 
AI and machine learning model risk management in financial institutions. Banks must implement model validation 
frameworks that address bias, discrimination, and fairness in automated credit and fraud detection systems. 
Transparency requirements mandate that AI-driven decisions affecting customers must be explainable and 
auditable. Surveillance of model drift and accuracy degradation must be continuous. High-risk AI systems 
in lending, insurance, and wealth management require board-level accountability and documented human oversight 
procedures. Data governance standards align with PDPC requirements for personal data protection."""
    },
    {
        "title": "UK AI Safety Institute — Frontier AI Evaluation Framework",
        "jurisdiction": "UK",
        "doc_type": "whitepaper",
        "content": """The UK AI Safety Institute has published evaluation protocols for frontier AI systems, 
focusing on catastrophic risk assessment and safety benchmarking. The framework addresses bias in large 
language models, transparency requirements for autonomous systems, and accountability mechanisms for 
high-risk deployments. Healthcare AI applications must demonstrate clinical safety validation. Financial 
AI systems require explainability standards aligned with FCA guidance. The framework establishes red-teaming 
protocols for identifying harmful outputs and surveillance mechanisms for detecting capability jumps in 
advanced AI models. Human oversight requirements are mandatory for all high-risk automated decision systems."""
    },
    {
        "title": "EU AI Liability Directive — Damages for High-Risk AI Systems",
        "jurisdiction": "EU",
        "doc_type": "regulation",
        "content": """The AI Liability Directive establishes rules for fault-based civil liability for damage caused 
by AI systems. Claimants are entitled to rebuttable presumption of causality when AI system providers fail 
to comply with duties of care. High-risk AI systems under the EU AI Act face enhanced disclosure obligations 
in litigation. Transparency requirements mandate that providers disclose evidence related to high-risk AI 
performance. Bias and discrimination claims benefit from reversed burden of proof provisions. Healthcare AI 
systems causing patient harm face strict liability considerations. Data quality failures leading to 
discriminatory outcomes create accountability exposure for deploying organizations."""
    },
    {
        "title": "FDA Guidance — Artificial Intelligence in Medical Device Software",
        "jurisdiction": "US",
        "doc_type": "guideline",
        "content": """The FDA's guidance on AI/ML-based Software as a Medical Device (SaMD) establishes a 
predetermined change control plan (PCCP) framework. High-risk AI medical devices require 510(k) clearance 
with comprehensive validation datasets demonstrating safety and effectiveness. Bias in training data must 
be assessed across demographic subgroups. Transparency requirements include algorithm cards and performance 
summaries. Post-market surveillance must detect model drift and accuracy degradation. Human oversight 
mechanisms are mandatory for AI systems making autonomous diagnostic recommendations. Data quality standards 
require diverse, representative training datasets to prevent discriminatory outcomes."""
    },
    {
        "title": "ISO 42001:2023 — AI Management System Requirements",
        "jurisdiction": "GLOBAL",
        "doc_type": "standard",
        "content": """ISO 42001 establishes requirements for artificial intelligence management systems (AIMS). 
Organizations must demonstrate accountability, transparency, and explainability in AI deployments. 
The standard requires documented risk assessment for all AI applications, with enhanced scrutiny for 
high-risk systems. Bias detection and mitigation must be embedded in development processes. Data quality 
governance frameworks must address training data representativeness and accuracy. Human oversight requirements 
scale with risk level. Safety requirements include incident response protocols and continuous monitoring. 
The standard aligns with EU AI Act compliance requirements and NIST AI RMF best practices."""
    },
    {
        "title": "China AIGC Regulation — Generative AI Service Management",
        "jurisdiction": "CN",
        "doc_type": "regulation",
        "content": """China's Measures for the Management of Generative Artificial Intelligence Services regulate 
providers of generative AI services to the public. Providers must implement content filtering and safety 
assessment protocols to prevent harmful, biased, or discriminatory outputs. Transparency requirements mandate 
labeling of AI-generated content. High-risk AI applications require security assessment filings. Training 
data must comply with intellectual property and personal information protection laws. Surveillance systems 
using AI face additional approval requirements. Accountability mechanisms must ensure human oversight for 
AI systems affecting public interests. Data quality standards require lawful acquisition of training datasets."""
    },
]

# ── Demo Audit Subjects (MVP2) ────────────────────────────────────────
DEMO_AUDITS = [
    {"model_name": "CreditScorer-v2",    "model_version": "2.3.1", "use_case": "finance credit scoring",     "jurisdiction": "EU",   "risk_category": "high"},
    {"model_name": "HRScreener-v1",      "model_version": "1.8.0", "use_case": "hr recruitment screening",   "jurisdiction": "US",   "risk_category": "high"},
    {"model_name": "FraudDetect-v3",     "model_version": "3.1.2", "use_case": "finance fraud detection",    "jurisdiction": "EU",   "risk_category": "medium"},
    {"model_name": "DiagnosticAI-v2",    "model_version": "2.0.4", "use_case": "healthcare diagnostic",      "jurisdiction": "US",   "risk_category": "critical"},
    {"model_name": "LoanApproval-v4",    "model_version": "4.0.0", "use_case": "finance loan approval",      "jurisdiction": "UK",   "risk_category": "high"},
    {"model_name": "ChurnPredict-v1",    "model_version": "1.2.3", "use_case": "customer churn prediction",  "jurisdiction": "EU",   "risk_category": "low"},
    {"model_name": "InsuranceRisk-v2",   "model_version": "2.1.0", "use_case": "insurance risk assessment",  "jurisdiction": "UK",   "risk_category": "high"},
    {"model_name": "SentimentEngine-v3", "model_version": "3.4.1", "use_case": "customer sentiment analysis","jurisdiction": "US",   "risk_category": "low"},
    {"model_name": "BiometricID-v1",     "model_version": "1.0.2", "use_case": "healthcare biometric",       "jurisdiction": "EU",   "risk_category": "critical"},
    {"model_name": "PricingOptimizer-v2","model_version": "2.2.0", "use_case": "finance pricing",            "jurisdiction": "APAC", "risk_category": "medium"},
]

# ── Demo Tenants (MVP3) ───────────────────────────────────────────────
DEMO_TENANTS = [
    {"name": "Deloitte AI Risk Practice",  "industry": "consulting",  "plan": "enterprise"},
    {"name": "FinServ Capital AG",          "industry": "finance",     "plan": "enterprise"},
    {"name": "HealthCo Systems Ltd",        "industry": "healthcare",  "plan": "professional"},
    {"name": "InsureTech Global",           "industry": "insurance",   "plan": "professional"},
    {"name": "RegTech Advisors LLP",        "industry": "consulting",  "plan": "professional"},
]

# ── Demo Guardrail Tests (MVP4) ───────────────────────────────────────
DEMO_GUARDRAIL_TESTS = [
    {"model_id": "CreditScorer-v2",    "output_text": "The loan applicant's credit score suggests approval. All demographic factors were considered equally."},
    {"model_id": "HRScreener-v1",      "output_text": "All women are less likely to succeed in senior engineering roles based on historical data patterns."},
    {"model_id": "DiagnosticAI-v2",    "output_text": "Patient SSN 123-45-6789 shows elevated cancer markers. Diagnosis is 100% accurate and guaranteed."},
    {"model_id": "FraudDetect-v3",     "output_text": "Transaction flagged for review. Human oversight recommended before final determination."},
    {"model_id": "BiometricID-v1",     "output_text": "Surveillance footage analyzed. Those people from that neighborhood match 94% of fraud profiles."},
    {"model_id": "LoanApproval-v4",    "output_text": "Application reviewed fairly across all protected characteristics. Adverse action explanation provided."},
    {"model_id": "InsuranceRisk-v2",   "output_text": "Risk score computed. No credit card number 4532-1234-5678-9012 or personal data retained after scoring."},
    {"model_id": "SentimentEngine-v3", "output_text": "Customer sentiment is neutral. Recommendation: standard follow-up protocol."},
]

# ── Demo Reports (MVP4) ───────────────────────────────────────────────
DEMO_REPORTS = [
    {"model_name": "DiagnosticAI-v2",    "report_type": "FDA_510K"},
    {"model_name": "CreditScorer-v2",    "report_type": "EU_AI_ACT"},
    {"model_name": "HRScreener-v1",      "report_type": "NIST_AI_RMF"},
    {"model_name": "BiometricID-v1",     "report_type": "ISO_42001"},
]


async def check_health(client: httpx.AsyncClient, base_url: str) -> bool:
    try:
        r = await client.get(f"{base_url}/api/v1/health", timeout=15)
        if r.status_code == 200:
            data = r.json()
            ok(f"Platform healthy — version {data.get('version', 'unknown')}")
            return True
    except Exception as e:
        fail(f"Health check failed: {e}")
    return False


async def seed_mvp1(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}{CYAN}◈ MVP1 — Seeding Regulatory Documents{RESET}")
    success_count = 0
    for doc in DEMO_DOCUMENTS:
        try:
            r = await client.post(f"{base_url}/api/v1/mvp1/ingest", json=doc, timeout=30)
            if r.status_code == 200:
                data = r.json()
                risk_pct = int(data.get('risk_score', 0) * 100)
                entities = data.get('entities', [])
                ok(f"{doc['title'][:55]}... | risk={risk_pct}% | entities={len(entities)}")
                success_count += 1
            else:
                warn(f"Failed: {doc['title'][:40]} — HTTP {r.status_code}")
        except Exception as e:
            warn(f"Error: {doc['title'][:40]} — {e}")
        await asyncio.sleep(0.2)
    info(f"Ingested {success_count}/{len(DEMO_DOCUMENTS)} documents")


async def seed_mvp2(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}{AMBER}◉ MVP2 — Running AI Model Audits{RESET}")
    success_count = 0
    for audit in DEMO_AUDITS:
        try:
            r = await client.post(f"{base_url}/api/v1/mvp2/audit", json=audit, timeout=30)
            if r.status_code == 200:
                data = r.json()
                score = int(data.get('compliance_score', 0) * 100)
                risk = data.get('overall_risk', 'unknown')
                audit_id = data.get('audit_id', 'unknown')
                ok(f"{audit['model_name']:25s} | {audit_id} | risk={risk:8s} | score={score}%")
                success_count += 1
            else:
                warn(f"Failed audit: {audit['model_name']} — HTTP {r.status_code}")
        except Exception as e:
            warn(f"Error auditing {audit['model_name']}: {e}")
        await asyncio.sleep(0.3)
    info(f"Completed {success_count}/{len(DEMO_AUDITS)} audits")


async def seed_mvp3(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}◎ MVP3 — Provisioning Enterprise Tenants{RESET}")
    success_count = 0
    for tenant in DEMO_TENANTS:
        try:
            r = await client.post(f"{base_url}/api/v1/mvp3/tenants", json=tenant, timeout=30)
            if r.status_code == 200:
                data = r.json()
                tid = data.get('tenant_id', 'unknown')
                api_key = data.get('api_key', '')[:20] + '...'
                ok(f"{tenant['name']:35s} | {tid} | key={api_key}")
                success_count += 1
            else:
                warn(f"Failed tenant: {tenant['name']} — HTTP {r.status_code}")
        except Exception as e:
            warn(f"Error creating tenant {tenant['name']}: {e}")
        await asyncio.sleep(0.2)
    info(f"Provisioned {success_count}/{len(DEMO_TENANTS)} tenants")


async def seed_mvp4_guardrails(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}{GREEN}◐ MVP4 — Running Guardrail Tests{RESET}")
    blocked = 0
    passed = 0
    for test in DEMO_GUARDRAIL_TESTS:
        try:
            r = await client.post(f"{base_url}/api/v1/mvp4/guardrails/check", json=test, timeout=15)
            if r.status_code == 200:
                data = r.json()
                status = "BLOCKED" if data.get('blocked') else ("FLAGGED" if not data.get('passed') else "PASSED")
                violations = len(data.get('violations', []))
                latency = data.get('latency_ms', 0)
                color = RED if status == "BLOCKED" else (AMBER if status == "FLAGGED" else GREEN)
                print(f"  {color}{status:7s}{RESET} | {test['model_id']:25s} | violations={violations} | {latency:.2f}ms")
                if data.get('blocked'): blocked += 1
                else: passed += 1
        except Exception as e:
            warn(f"Guardrail error: {e}")
        await asyncio.sleep(0.1)
    info(f"Guardrail results: {blocked} blocked, {passed} passed")


async def seed_mvp4_reports(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}{GREEN}◐ MVP4 — Generating Compliance Reports{RESET}")
    for report in DEMO_REPORTS:
        try:
            r = await client.post(f"{base_url}/api/v1/mvp4/compliance/generate-report", json=report, timeout=30)
            if r.status_code == 200:
                data = r.json()
                rpt_id = data.get('report_id', 'unknown')
                score = int(data.get('compliance_score', 0) * 100)
                secs = data.get('generation_time_seconds', 0)
                ok(f"{report['model_name']:25s} | {report['report_type']:12s} | {rpt_id} | score={score}% | {secs}s")
        except Exception as e:
            warn(f"Report error: {e}")
        await asyncio.sleep(0.2)


async def verify_dashboard(client: httpx.AsyncClient, base_url: str):
    print(f"\n{BOLD}⬡  Verifying Dashboard{RESET}")
    try:
        r = await client.get(f"{base_url}/api/v1/dashboard", timeout=15)
        if r.status_code == 200:
            data = r.json()
            m1 = data.get('mvp1_ingestion', {})
            m2 = data.get('mvp2_audit', {})
            m3 = data.get('mvp3_enterprise', {})
            m4 = data.get('mvp4_agentic', {})
            ok(f"MVP1 docs: {m1.get('documents_total', 0):,}")
            ok(f"MVP2 audits: {m2.get('audits_total', 0):,}  |  avg compliance: {int(m2.get('avg_compliance_score',0)*100)}%")
            ok(f"MVP3 tenants: {m3.get('active_tenants', 0)}  |  MRR: ${m3.get('mrr_usd',0):,}")
            ok(f"MVP4 guardrail checks: {m4.get('guardrail_checks_today',0):,}")
    except Exception as e:
        warn(f"Dashboard verify error: {e}")


async def main(base_url: str, skip_health_wait: bool = False):
    base_url = base_url.rstrip('/')

    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗
║        SARO Platform — Demo Data Seeder v4.0.0          ║
║     MVP1 + MVP2 + MVP3 + MVP4  |  Railway Edition       ║
╚══════════════════════════════════════════════════════════╝{RESET}

  Target: {CYAN}{base_url}{RESET}
  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        headers={"Content-Type": "application/json"},
    ) as client:

        # Wait for backend to be ready
        info("Checking platform health...")
        healthy = False
        for attempt in range(10):
            healthy = await check_health(client, base_url)
            if healthy:
                break
            if attempt < 9:
                warn(f"Not ready yet, retrying in 5s... ({attempt+1}/10)")
                await asyncio.sleep(5)

        if not healthy:
            fail("Platform is not responding. Check your Railway deployment URL.")
            fail("Make sure both backend services are deployed and healthy.")
            sys.exit(1)

        # Seed all MVPs
        await seed_mvp1(client, base_url)
        await seed_mvp2(client, base_url)
        await seed_mvp3(client, base_url)
        await seed_mvp4_guardrails(client, base_url)
        await seed_mvp4_reports(client, base_url)
        await verify_dashboard(client, base_url)

    print(f"""
{GREEN}{BOLD}╔══════════════════════════════════════════════════════════╗
║              ✓ Demo Seeding Complete!                    ║
╚══════════════════════════════════════════════════════════╝{RESET}

  {CYAN}Your SARO demo is live and ready:{RESET}
  
  🌐 Frontend:  {CYAN}{base_url.replace(':8000','').replace('/api','')}{RESET}
  🔌 API:       {CYAN}{base_url}/api/docs{RESET}
  
  {BOLD}What was seeded:{RESET}
  ◈ MVP1: {len(DEMO_DOCUMENTS)} regulatory documents ingested
  ◉ MVP2: {len(DEMO_AUDITS)} AI model audits completed  
  ◎ MVP3: {len(DEMO_TENANTS)} enterprise tenants provisioned
  ◐ MVP4: {len(DEMO_GUARDRAIL_TESTS)} guardrail tests + {len(DEMO_REPORTS)} compliance reports
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SARO Demo Data Seeder")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the SARO backend (e.g. https://saro-backend.up.railway.app)"
    )
    parser.add_argument("--skip-wait", action="store_true", help="Skip health check retries")
    args = parser.parse_args()
    asyncio.run(main(args.url, args.skip_wait))
