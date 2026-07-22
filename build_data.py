#!/usr/bin/env python3
"""
Convert a real rfp-tracker CSV export into the web app's data feed.

Usage:
    # In the rfp-tracker repo, produce a CSV:
    python3 rfp.py fetch
    python3 rfp.py export --file rfps.csv

    # Then convert it for the site:
    python3 build_data.py rfps.csv

This writes data/rfps.json next to the site. Only public opportunity fields
are included — internal Status / Assignee / Notes columns are intentionally
dropped so nothing internal is published.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

TYPE_FROM_LABEL = {
    "Federal Contract (SAM.gov)": "gov_federal",
    "State/Local Gov RFP": "state_local",
    "Brand Agency Search": "brand_lead",
}


def domain_of(url: str) -> str:
    m = re.search(r"https?://([^/]+)", url or "")
    return m.group(1) if m else ""


def convert(csv_path: str) -> dict:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), 1):
            type_label = (row.get("Type") or "").strip()
            rows.append({
                "id": f"rfp-{i:04d}",
                "type": TYPE_FROM_LABEL.get(type_label, "perplexity"),
                "title": (row.get("Title") or "").strip(),
                "issuer": (row.get("Issuer") or "").strip(),
                "posted": (row.get("Posted") or "").strip(),
                "deadline": (row.get("Deadline") or "").strip(),
                "url": (row.get("Application Link") or "").strip(),
                "source_domain": domain_of(row.get("Application Link") or ""),
                "description": "",  # CSV export has no description column
            })
    # Drop rows with no title
    rows = [r for r in rows if r["title"]]
    return {"generated": date.today().isoformat(), "rfps": rows}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    out = Path(__file__).parent / "data" / "rfps.json"
    data = convert(sys.argv[1])
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {len(data['rfps'])} RFPs → {out}")


if __name__ == "__main__":
    main()
