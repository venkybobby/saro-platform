"""
import_mit_risks.py — One-shot importer for the MIT AI Risk Repository
======================================================================
Reads the MIT "AI Risk Database v3" Excel sheet and writes all rows into
the persistent `mit_risks` table via SQLAlchemy.

Run ONCE after alembic upgrade head:

  pip install pandas openpyxl sqlalchemy psycopg2-binary
  python import_mit_risks.py --excel "The AI Risk Repository V3_26_03_2025.xlsx"

Falls back to inserting the 200 synthetic cases from test_data_mit_200.json
if no Excel file is provided (useful for CI / demo environments).

Environment variable DATABASE_URL must be set, or pass --db flag.
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


# ── Domain normalisation map ─────────────────────────────────────────────────
# Maps raw Excel "Domain" values to SARO's canonical 7-domain taxonomy.
DOMAIN_NORMALISE = {
    "Discrimination & Toxicity":    "Discrimination & Toxicity",
    "Privacy & Security":           "Privacy & Security",
    "Misinformation":               "Misinformation",
    "Malicious Use":                "Malicious Use",
    "Human-Computer Interaction":   "Human-Computer Interaction",
    "Socioeconomic & Environmental": "Socioeconomic & Environmental",
    "AI System Safety":             "AI System Safety",
    # Common alternate spellings / short-forms in the Excel:
    "Discrimination":               "Discrimination & Toxicity",
    "Toxicity":                     "Discrimination & Toxicity",
    "Privacy":                      "Privacy & Security",
    "Security":                     "Privacy & Security",
    "Misinformation & Disinformation": "Misinformation",
    "Socioeconomic":                "Socioeconomic & Environmental",
    "Environmental":                "Socioeconomic & Environmental",
    "Safety":                       "AI System Safety",
    "HCI":                          "Human-Computer Interaction",
}

ALL_DOMAINS = list({v for v in DOMAIN_NORMALISE.values()})


def _normalise_domain(raw: str) -> str:
    """Return canonical domain string; default AI System Safety if unrecognised."""
    if not raw or not isinstance(raw, str):
        return "AI System Safety"
    raw = raw.strip()
    return DOMAIN_NORMALISE.get(raw, raw if raw in ALL_DOMAINS else "AI System Safety")


def load_from_excel(excel_path: str) -> list[dict]:
    """Parse MIT AI Risk Repository Excel file into list of row dicts."""
    try:
        import pandas as pd
    except ImportError:
        print("ERROR: pandas not installed. Run: pip install pandas openpyxl")
        sys.exit(1)

    path = Path(excel_path)
    if not path.exists():
        print(f"ERROR: Excel file not found: {excel_path}")
        sys.exit(1)

    print(f"Reading Excel: {excel_path} …")
    try:
        df = pd.read_excel(excel_path, sheet_name="AI Risk Database v3")
    except Exception as e:
        print(f"ERROR reading sheet: {e}")
        sys.exit(1)

    print(f"  Raw rows loaded: {len(df)}")

    # Determine which columns exist (column names vary slightly across versions)
    col_map = {
        "ev_id":            next((c for c in df.columns if "Ev_ID"     in str(c) or "ev_id"  in str(c).lower()), None),
        "paper_id":         next((c for c in df.columns if "Paper_ID"  in str(c) or "paper"  in str(c).lower()), None),
        "category_level":   next((c for c in df.columns if "Category level" in str(c) or "category_level" in str(c).lower()), None),
        "risk_category":    next((c for c in df.columns if "Risk category"  in str(c) and "sub" not in str(c).lower()), None),
        "risk_subcategory": next((c for c in df.columns if "Risk subcategory" in str(c) or "subcategory" in str(c).lower()), None),
        "description":      next((c for c in df.columns if "Description" in str(c)), None),
        "additional_ev":    next((c for c in df.columns if "Additional" in str(c)), None),
        "entity":           next((c for c in df.columns if "Entity"  in str(c)), None),
        "intent":           next((c for c in df.columns if "Intent"  in str(c)), None),
        "timing":           next((c for c in df.columns if "Timing"  in str(c)), None),
        "domain":           next((c for c in df.columns if "Domain"  in str(c)), None),
        "sub_domain":       next((c for c in df.columns if "Sub-domain" in str(c) or "sub_domain" in str(c).lower()), None),
    }

    def _get(row, key, default=""):
        col = col_map.get(key)
        if col is None:
            return default
        val = row.get(col, default)
        import pandas as _pd
        if _pd.isna(val):
            return default
        return str(val).strip()

    rows = []
    for idx, row in df.iterrows():
        desc = _get(row, "description")
        if not desc:
            continue  # skip blank rows
        rows.append({
            "ev_id":            _get(row, "ev_id",            f"MIT-{idx+1:05d}"),
            "paper_id":         _get(row, "paper_id"),
            "category_level":   _get(row, "category_level"),
            "risk_category":    _get(row, "risk_category"),
            "risk_subcategory": _get(row, "risk_subcategory"),
            "description":      desc[:2000],
            "additional_ev":    _get(row, "additional_ev")[:1000] if _get(row, "additional_ev") else "",
            "causal_entity":    _get(row, "entity",  "Developer"),
            "causal_intent":    _get(row, "intent",  "Unintentional"),
            "causal_timing":    _get(row, "timing",  "Post-deployment"),
            "domain":           _normalise_domain(_get(row, "domain")),
            "sub_domain":       _get(row, "sub_domain"),
        })

    print(f"  Parsed {len(rows)} non-empty rows")
    return rows


def load_from_json(json_path: str) -> list[dict]:
    """Fallback: load synthetic test_data_mit_200.json and convert to DB row format."""
    path = Path(json_path)
    if not path.exists():
        print(f"ERROR: JSON file not found: {json_path}")
        sys.exit(1)

    with open(path) as f:
        cases = json.load(f)

    rows = []
    for i, c in enumerate(cases):
        rows.append({
            "ev_id":            c.get("risk_id", f"SYN-{i+1:04d}"),
            "paper_id":         "synthetic",
            "category_level":   "Synthetic",
            "risk_category":    c.get("domain", ""),
            "risk_subcategory": c.get("sub_domain", ""),
            "description":      c.get("description", ""),
            "additional_ev":    c.get("mitigation_hint", ""),
            "causal_entity":    c.get("causal", {}).get("entity",  "Developer"),
            "causal_intent":    c.get("causal", {}).get("intent",  "Unintentional"),
            "causal_timing":    c.get("causal", {}).get("timing",  "Post-deployment"),
            "domain":           _normalise_domain(c.get("domain", "")),
            "sub_domain":       c.get("sub_domain", ""),
        })
    return rows


def import_to_db(rows: list[dict], database_url: str, clear_first: bool = False) -> int:
    """Write rows into mit_risks table. Returns count inserted."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
    except ImportError:
        print("ERROR: sqlalchemy not installed. Run: pip install sqlalchemy psycopg2-binary")
        sys.exit(1)

    engine  = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db      = Session()

    try:
        if clear_first:
            print("  Clearing existing mit_risks rows …")
            db.execute(text("DELETE FROM mit_risks"))
            db.commit()

        now = datetime.utcnow()
        inserted = 0

        # Batch insert in chunks of 200
        CHUNK = 200
        for start in range(0, len(rows), CHUNK):
            chunk = rows[start:start + CHUNK]
            db.execute(
                text("""
                    INSERT INTO mit_risks
                        (ev_id, paper_id, category_level, risk_category, risk_subcategory,
                         description, additional_ev, causal_entity, causal_intent,
                         causal_timing, domain, sub_domain, created_at, updated_at)
                    VALUES
                        (:ev_id, :paper_id, :category_level, :risk_category, :risk_subcategory,
                         :description, :additional_ev, :causal_entity, :causal_intent,
                         :causal_timing, :domain, :sub_domain, :created_at, :updated_at)
                """),
                [
                    {**r, "created_at": now, "updated_at": now}
                    for r in chunk
                ],
            )
            db.commit()
            inserted += len(chunk)
            print(f"  Inserted {inserted}/{len(rows)} rows …")

        return inserted

    finally:
        db.close()


def print_domain_summary(rows: list[dict]) -> None:
    from collections import Counter
    counts = Counter(r["domain"] for r in rows)
    print("\nDomain breakdown:")
    for domain, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {domain:<40} {count:>5}")


def main():
    parser = argparse.ArgumentParser(
        description="Import MIT AI Risk Repository into the SARO mit_risks table"
    )
    parser.add_argument(
        "--excel", type=str, default=None,
        help="Path to MIT AI Risk Repository Excel file (AI Risk Database v3 sheet)"
    )
    parser.add_argument(
        "--json", type=str, default="test_data_mit_200.json",
        help="Fallback JSON file path (synthetic test cases)"
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help="PostgreSQL DATABASE_URL (overrides DATABASE_URL env var)"
    )
    parser.add_argument(
        "--clear", action="store_true", default=False,
        help="Clear existing mit_risks rows before inserting (idempotent re-import)"
    )
    args = parser.parse_args()

    database_url = args.db or os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("ERROR: DATABASE_URL not set. Use --db flag or set DATABASE_URL env var.")
        sys.exit(1)

    # Load rows from Excel or fall back to JSON
    if args.excel:
        rows = load_from_excel(args.excel)
    else:
        fallback = args.json
        if not Path(fallback).exists():
            fallback = str(Path(__file__).parent / "test_data_mit_200.json")
        print(f"No --excel provided. Loading synthetic cases from {fallback}")
        rows = load_from_json(fallback)

    if not rows:
        print("No rows to import. Exiting.")
        sys.exit(1)

    print_domain_summary(rows)

    print(f"\nImporting {len(rows)} rows into mit_risks …")
    count = import_to_db(rows, database_url, clear_first=args.clear)

    print(f"\n✅ Import complete — {count} MIT risks stored in mit_risks table")
    print("   Run 'alembic upgrade head' first if the table does not exist yet.")


if __name__ == "__main__":
    main()
