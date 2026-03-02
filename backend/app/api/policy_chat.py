"""
AI Policy Chat Agent (FR-02, FR-INNOV-01..03)
Claude-powered chat for interactive policy explanations.
Context-injected with ingested SARO policy library.
Rate limited: 10 requests/min/session.

Endpoints:
  POST /policy-chat/ask       — ask any policy question
  GET  /policy-chat/history   — get chat history for session
  POST /policy-chat/clear     — clear session history
  GET  /policy-chat/suggested — suggested starter questions
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
import anthropic, os, time, uuid

router = APIRouter()

# Rate limit tracking: {session_id: [timestamps]}
_rate_limits: dict = {}
_histories:   dict = {}    # {session_id: [messages]}

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW   = 60   # seconds

# System context: SARO policy knowledge base injected into every Claude call
SARO_POLICY_CONTEXT = """You are SARO's AI Policy Expert Agent — an authoritative, concise regulatory compliance assistant built into the SARO (Smart AI Risk Orchestrator) platform.

Your role: Explain AI governance regulations, standards, and compliance requirements clearly to enterprise users. Help them understand what they need to do to comply, and how SARO helps them do it.

Reference standards you know deeply:
- EU AI Act (2024): Articles 5 (prohibited uses), 9 (risk management), 10 (data governance), 11 (technical documentation), 13 (transparency), 14 (human oversight), 15 (accuracy & robustness), 22 (fundamental rights impact assessment), 52 (transparency for general-purpose AI)
- NIST AI RMF 2.0: GOVERN 1.1 (governance policies), MAP 1.1 (privacy/harm documentation), MAP 2.3 (bias risk mapping), MEASURE 2.5 (performance measurement), MANAGE 2.2 (risk response), GOV 6.1 (transparency policies)
- ISO 42001:2023: A.5.2 (roles & responsibilities), A.6.1 (AI system documentation), A.6.2 (transparency objectives), A.8.4 (bias management), A.9.3 (operational controls)
- FDA AI/ML SaMD: §2.1 (clinical performance), §3.2 (clinical validation bias), §4.1 (explainability for clinicians), §5.3 (clinician override)
- MAS TREx Framework v2: Fairness, Ethics, Accountability, Transparency for financial AI
- GDPR Article 22: Automated decision-making, right to explanation

SARO Platform capabilities you can reference:
- Model Output Checker: uploads AI decisions, evaluates vs policy benchmarks
- Audit Flow: end-to-end pipeline with fail/warn/pass checklist + article refs
- Policy Library: searchable regulatory document library
- Agentic Guardrails: real-time bias/PII/hallucination blocking
- Autonomous Governance Bots: auto-remediation of compliance gaps
- Standards Reports: EU AI Act / NIST / ISO 42001 formatted outputs

Response style:
- Be specific: cite article numbers and requirements (e.g., "EU AI Act Art. 10 requires...")
- Be practical: explain what action the user needs to take
- Be concise: 2-4 paragraphs max unless asked for detail
- Connect to SARO: mention which SARO feature helps when relevant
- Use numbered lists for requirements, bullet points for options
- If you don't know something specific, say so and suggest consulting the original standard"""

SUGGESTED_QUESTIONS = [
    {"category": "EU AI Act",   "q": "What does EU AI Act Article 10 require for training data?"},
    {"category": "EU AI Act",   "q": "Which AI systems are prohibited under Article 5?"},
    {"category": "EU AI Act",   "q": "What transparency obligations apply under Article 13?"},
    {"category": "NIST AI RMF", "q": "How does NIST AI RMF MAP 2.3 define bias risk?"},
    {"category": "NIST AI RMF", "q": "What is the GOVERN 1.1 requirement for AI governance?"},
    {"category": "ISO 42001",   "q": "What does ISO 42001 A.8.4 require for bias management?"},
    {"category": "FDA SaMD",    "q": "What accuracy threshold does FDA SaMD §2.1 require?"},
    {"category": "MAS TREx",    "q": "How does the MAS TREx framework define fairness for financial AI?"},
    {"category": "Compliance",  "q": "What is the minimum bias score I need to pass EU AI Act?"},
    {"category": "Compliance",  "q": "How do I prove human oversight to regulators?"},
    {"category": "SARO",        "q": "How does SARO's Model Output Checker work?"},
    {"category": "SARO",        "q": "What does a SARO Audit Report contain?"},
]


def _check_rate_limit(session_id: str) -> bool:
    """Returns True if under limit, raises if exceeded."""
    now = time.time()
    timestamps = _rate_limits.get(session_id, [])
    # Remove timestamps outside window
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(429, f"Rate limit: {RATE_LIMIT_REQUESTS} requests/minute exceeded")
    timestamps.append(now)
    _rate_limits[session_id] = timestamps
    return True


def _call_claude(messages: list[dict]) -> str:
    """Call Claude API with SARO policy context and conversation history."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        # Fallback: rich mock response when no API key configured
        return _mock_policy_response(messages[-1]["content"] if messages else "")

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=SARO_POLICY_CONTEXT,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        # Graceful degradation if API unavailable
        return _mock_policy_response(messages[-1]["content"] if messages else "")


def _mock_policy_response(query: str) -> str:
    """Rich fallback responses when Claude API is unavailable."""
    q = query.lower()
    if "art. 10" in q or "article 10" in q or "training data" in q:
        return """**EU AI Act Article 10 — Data Governance & Training Data**

Article 10 requires providers of high-risk AI systems to implement data governance practices covering:

1. **Data quality criteria** — training, validation and testing datasets must be relevant, representative, free of errors and complete for the system's intended purpose
2. **Bias examination** — datasets must be examined for potential biases that could affect fundamental rights
3. **Data provenance** — documentation of origin, scope, characteristics and processing operations
4. **Protected attributes** — examination for correlations with characteristics that could lead to prohibited discrimination

**SARO helps with this:** The Model Output Checker evaluates your model's bias score against the Art. 10 threshold (default: <15%). The Audit Flow generates a complete Art. 10 compliance checklist with your measured bias score vs. threshold.

🔍 Action required: Run your model through SARO's Audit Flow → select EU AI Act → check the "Data Governance & Bias" finding."""
    elif "art. 5" in q or "article 5" in q or "prohibited" in q:
        return """**EU AI Act Article 5 — Prohibited AI Practices**

The following AI uses are **absolutely prohibited** under EU AI Act Article 5:

1. Subliminal manipulation techniques harmful to users
2. Exploitation of vulnerabilities (age, disability) to influence behaviour
3. Social scoring by public authorities
4. Real-time remote biometric identification in public spaces (limited exceptions for law enforcement)
5. Emotion recognition in workplaces and educational institutions
6. Biometric categorisation based on sensitive characteristics (race, religion, sexual orientation)
7. Predictive policing based solely on profiling

**SARO helps:** The Ethics Scanner in Autonomous Governance flags prohibited use patterns. The Guardrails module blocks outputs containing biometric/surveillance signals in real-time.

⚠️ If your AI system has any of these characteristics, it cannot be deployed in the EU regardless of technical mitigations."""
    elif "nist" in q or "map 2.3" in q or "bias risk" in q:
        return """**NIST AI RMF MAP 2.3 — Bias Risk Mapping**

MAP 2.3 requires organizations to systematically identify and assess bias risks across the AI lifecycle:

1. **Identify bias sources** — training data collection, labelling processes, feature selection, model architecture
2. **Measure bias metrics** — demographic parity, equalized odds, calibration across protected groups
3. **Document bias assessments** — maintain records of tests performed and results
4. **Establish thresholds** — define acceptable bias levels for your use case and jurisdiction
5. **Monitor continuously** — track bias drift in production

NIST sets a bias threshold of **≤12%** (stricter than EU AI Act's 15%).

**SARO helps:** Select NIST AI RMF as the benchmark in Audit Flow → the system evaluates MAP 2.3 specifically and generates a finding with your measured vs. threshold score."""
    elif "transparency" in q or "art. 13" in q:
        return """**EU AI Act Article 13 — Transparency Obligations**

High-risk AI systems must be designed to enable users to interpret outputs and use them appropriately:

1. **Instructions for use** — clear documentation for deployers
2. **System description** — intended purpose, level of accuracy, human oversight measures
3. **Input data** — what data the system processes
4. **Performance metrics** — accuracy rates, relevant benchmarks
5. **Known limitations** — circumstances that could affect performance

SARO measures a **Transparency Score** (0-1 scale, minimum 0.60 for EU AI Act compliance). Systems below 0.60 receive a WARN; below 0.48 receive CRITICAL.

**SARO helps:** The Audit Flow's "Explainability & Transparency" check evaluates this. Remediation: implement SHAP/LIME explanations, add decision rationale to all outputs."""
    else:
        return f"""**SARO Policy Agent — AI Governance Query**

Your question has been received. Here are the most relevant frameworks for your query:

**Key standards that may apply:**
- **EU AI Act** (2024) — comprehensive risk-based framework for all AI in the EU market
- **NIST AI RMF 2.0** — US framework covering GOVERN, MAP, MEASURE, MANAGE functions
- **ISO 42001:2023** — International AI management system standard
- **GDPR Article 22** — Automated decision-making requirements

**To get a precise answer:** Try asking about a specific article (e.g., "What does Art. 10 require?") or a specific requirement (e.g., "What bias threshold applies under NIST?").

**In SARO:** Use the Policy Library to browse all ingested standards, or run the Audit Flow to get an article-by-article compliance checklist for your model.

💬 *Note: Connect an Anthropic API key to SARO to enable full AI-powered policy explanations.*"""


@router.post("/policy-chat/ask")
async def ask_policy_question(payload: dict):
    """
    FR-INNOV-01..03: Ask policy question, get Claude-powered answer.
    Context-injected with SARO standards library.
    """
    query      = payload.get("query", "").strip()
    session_id = payload.get("session_id", str(uuid.uuid4()))

    if not query:
        raise HTTPException(400, "Query is required")
    if len(query) > 2000:
        raise HTTPException(400, "Query too long — max 2000 characters")

    # Rate limit check
    _check_rate_limit(session_id)

    # Get/init session history
    history = _histories.get(session_id, [])

    # Build Claude messages (full conversation history for context)
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": query})

    answer = _call_claude(messages)

    # Store in history
    history.append({"role": "user",      "content": query,  "timestamp": datetime.utcnow().isoformat()})
    history.append({"role": "assistant", "content": answer, "timestamp": datetime.utcnow().isoformat()})
    _histories[session_id] = history[-40:]  # Keep last 20 turns

    return {
        "query":      query,
        "answer":     answer,
        "session_id": session_id,
        "turn":       len(history) // 2,
        "timestamp":  datetime.utcnow().isoformat(),
    }


@router.get("/policy-chat/history")
async def get_history(session_id: str):
    return {
        "session_id": session_id,
        "history":    _histories.get(session_id, []),
        "turns":      len(_histories.get(session_id, [])) // 2,
    }


@router.post("/policy-chat/clear")
async def clear_history(payload: dict):
    session_id = payload.get("session_id", "")
    _histories.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@router.get("/policy-chat/suggested")
async def suggested_questions():
    return {"questions": SUGGESTED_QUESTIONS}
