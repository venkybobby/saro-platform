# SARO Nightly Regression CI Setup

To enable the nightly 100-flow regression (FR-TEST-01..03):

1. In GitHub: Settings → Actions → ensure Actions are enabled
2. Copy `nightly-regression.yaml` → `.github/workflows/nightly-regression.yaml`
3. Copy `regression_100flows.py` → `.github/scripts/regression_100flows.py`

Or use a PAT with `workflow` scope to push `.github/` directly.

The workflow runs nightly at 03:00 UTC (9:00 PM CST) and:
- Runs 100 E2E flows against the deployed Koyeb backend
- Fails if mitigation < 70%, latency > 30s, or error rate > 5%
