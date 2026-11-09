#!/usr/bin/env python3
"""Screen normalized Flippa listing claims for manual acquisition diligence."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

PUBLIC_FIELDS = {"listing_id", "title", "category", "asking_price", "monthly_profit", "age_months", "monthly_traffic", "source_url", "captured_at"}


def csv_cell(value):
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(("=", "+", "-", "@", "\t", "\r")) else text


def parse_money(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\s*[$€£]?\s*([\d,]+(?:\.\d+)?)\s*([kKmM]?)\s*", value)
    if not match:
        return None
    return float(match.group(1).replace(",", "")) * {"": 1, "k": 1_000, "m": 1_000_000}[match.group(2).lower()]


def profit_multiple(price, monthly_profit):
    price_value, profit_value = parse_money(price), parse_money(monthly_profit)
    if not price_value or not profit_value or profit_value <= 0:
        return None
    return round(price_value / (profit_value * 12), 2)


def public_record(record):
    return {k: v for k, v in record.items() if k in PUBLIC_FIELDS}


def normalize_listings(records):
    deduped = {}
    for raw in records:
        row = public_record(raw)
        identity = str(row.get("listing_id", "")).strip()
        if not identity:
            raise ValueError("Every listing needs a listing_id from its public URL")
        row["listing_id"] = identity
        row["asking_price"] = parse_money(row.get("asking_price"))
        row["monthly_profit"] = parse_money(row.get("monthly_profit"))
        row["annual_profit_multiple"] = profit_multiple(row["asking_price"], row["monthly_profit"])
        deduped[identity] = row
    return [deduped[key] for key in sorted(deduped)]


def screen_listing(row, criteria):
    flags = ["seller_claims_not_independently_verified"]
    required = {"asking_price": "price_not_disclosed", "monthly_profit": "profit_not_disclosed", "age_months": "age_not_disclosed", "monthly_traffic": "traffic_not_disclosed"}
    for field, flag in required.items():
        if row.get(field) is None:
            flags.append(flag)
    if row.get("asking_price") is not None and row["asking_price"] <= 0:
        flags.append("price_not_positive")
    if row.get("monthly_profit") is not None and row["monthly_profit"] <= 0:
        flags.append("profit_not_positive")
    exclusion_reasons = []
    if criteria.get("max_price") is not None and row.get("asking_price") is not None and row["asking_price"] > criteria["max_price"]:
        exclusion_reasons.append("price_above_max")
    if criteria.get("min_monthly_profit") is not None and row.get("monthly_profit") is not None and row["monthly_profit"] < criteria["min_monthly_profit"]:
        exclusion_reasons.append("profit_below_min")
    if criteria.get("max_multiple") is not None and row.get("annual_profit_multiple") is not None and row["annual_profit_multiple"] > criteria["max_multiple"]:
        exclusion_reasons.append("multiple_above_max")
    core_missing = row.get("asking_price") is None or row.get("monthly_profit") is None or row.get("annual_profit_multiple") is None
    decision = "excluded" if exclusion_reasons else ("evidence_gap" if core_missing else "manual_diligence")
    result = dict(row)
    result.update({"decision": decision, "flags": flags, "exclusion_reasons": exclusion_reasons})
    return result


def comparison_value(value):
    if isinstance(value, dict):
        return {k: comparison_value(v) for k, v in value.items() if k not in {"status", "captured_at"}}
    if isinstance(value, list):
        return [comparison_value(v) for v in value]
    return value


def md(value):
    return " ".join(str(value if value is not None else "").split()).replace("|", "\\|")


def render(result):
    lines = ["# Flippa Deal Screener | Powered by Bright Data", "", "Listing figures are seller or marketplace claims and are not independently verified. This is a diligence queue, not a valuation, recommendation, or purchase decision.", "", "| Listing | Price | Monthly profit | Annual multiple | Decision | Flags | Status |", "|---|---:|---:|---:|---|---|---|"]
    for row in result["rows"]:
        lines.append(f"| {md(row.get('title', row['listing_id']))} | {row.get('asking_price') if row.get('asking_price') is not None else 'unknown'} | {row.get('monthly_profit') if row.get('monthly_profit') is not None else 'unknown'} | {row.get('annual_profit_multiple') if row.get('annual_profit_multiple') is not None else 'unknown'} | {row['decision']} | {', '.join(row['flags'])} | {row['status']} |")
    if result["markets"]:
        lines += ["", "## Displayed category context", "", "Category counts are marketplace labels at capture time, not demand or transaction volume."]
        for row in result["markets"]:
            lines.append(f"- {md(row.get('category'))}: {row.get('displayed_listing_count', 'unknown')} displayed listings")
    return "\n".join(lines) + "\n"


def render_diligence(rows):
    lines = ["# Flippa manual diligence checklist | Powered by Bright Data", "", "Use this as a request list for human diligence. It is not a valuation, legal review, or purchase recommendation.", ""]
    if not rows:
        lines.append("No listings were supplied.")
    checks = {
        "seller_claims_not_independently_verified": "Verify displayed price and profit against independent financial and platform records.",
        "price_not_disclosed": "Obtain the current asking price and any fees.",
        "profit_not_disclosed": "Obtain a profit-and-loss statement and reconcile claimed monthly profit.",
        "age_not_disclosed": "Verify the business age with founding and ownership records.",
        "traffic_not_disclosed": "Verify monthly traffic with read-only analytics evidence.",
        "price_not_positive": "Resolve the non-positive asking price before calculating economics.",
        "profit_not_positive": "Resolve the non-positive monthly profit before calculating economics.",
    }
    for row in rows:
        lines += [f"## {md(row.get('title') or row['listing_id'])} — {row['decision']}", "", f"Source: {md(row.get('source_url') or 'not captured')}", ""]
        if row["decision"] == "excluded":
            lines += [f"- Mechanical exclusion: {', '.join(row['exclusion_reasons'])}.", "- Change the buy-box criteria and rerun if you want to reconsider; do not silently override the rule.", ""]
            continue
        lines.append("### Resolve before any offer")
        lines.append("")
        lines += [f"- [ ] {checks[flag]}" for flag in row["flags"] if flag in checks]
        lines += ["- [ ] Confirm ownership, authority to sell, transfer obligations, and included assets.", "- [ ] Reconcile revenue, expenses, refunds, churn, traffic sources, and concentration risks.", "- [ ] Obtain qualified legal, tax, and financial review before any bid or offer.", ""]
    return "\n".join(lines) + "\n"


def analyze(payload, previous=None):
    criteria = payload.get("criteria", {})
    rows = [screen_listing(r, criteria) for r in normalize_listings(payload.get("rows", []))]
    old = {r["listing_id"]: comparison_value(r) for r in (previous or {}).get("rows", [])}
    for row in rows:
        identity = row["listing_id"]
        row["status"] = "new" if identity not in old else ("unchanged" if old[identity] == comparison_value(row) else "changed")
    markets = [{k: v for k, v in m.items() if k in {"category", "displayed_listing_count", "source_url", "captured_at"}} for m in payload.get("markets", [])]
    run_id = hashlib.sha256(json.dumps(comparison_value({"rows": rows, "markets": markets}), sort_keys=True).encode()).hexdigest()[:12]
    result = {"rows": rows, "markets": markets, "snapshot": {"schema_version": 1, "run_id": run_id, "criteria": criteria, "rows": rows, "markets": markets}}
    result["report"] = render(result)
    result["diligence"] = render_diligence(rows)
    return result


def write_outputs(result, output_dir):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(result["report"])
    (out / "run.json").write_text(json.dumps(result["snapshot"], indent=2, sort_keys=True) + "\n")
    (out / "diligence.md").write_text(result["diligence"])
    fields = ["listing_id", "title", "category", "asking_price", "monthly_profit", "annual_profit_multiple", "age_months", "monthly_traffic", "decision", "flags", "exclusion_reasons", "status", "source_url", "captured_at"]
    with (out / "listings.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in result["rows"]:
            writer.writerow({key: csv_cell(json.dumps(row[key]) if key in {"flags", "exclusion_reasons"} else row.get(key)) for key in fields})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--previous", help="Prior run.json; omit on the first run")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    payload = json.loads(Path(args.input).read_text())
    previous = json.loads(Path(args.previous).read_text()) if args.previous else None
    write_outputs(analyze(payload, previous), args.output_dir)


if __name__ == "__main__":
    main()
