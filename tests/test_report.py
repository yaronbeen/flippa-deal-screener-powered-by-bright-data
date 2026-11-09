import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from report import analyze, csv_cell, normalize_listings, profit_multiple, screen_listing, write_outputs


class FlippaTests(unittest.TestCase):
    def test_multiple_requires_positive_monthly_profit(self):
        self.assertEqual(profit_multiple("$120k", "$10k"), 1.0)
        self.assertIsNone(profit_multiple("$120k", "undisclosed"))
        self.assertIsNone(profit_multiple("$120k", 0))

    def test_dedupe_and_seller_identity_stripping(self):
        rows = [
            {"listing_id": "123", "title": "Acme SaaS", "asking_price": "$10k", "monthly_profit": "$500", "seller": "A Person"},
            {"listing_id": "123", "title": "Acme SaaS", "asking_price": "$12k", "monthly_profit": "$1k", "seller_email": "person@example.com"},
        ]
        clean = normalize_listings(rows)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["asking_price"], 12000.0)
        self.assertNotIn("person", json.dumps(clean).lower())
        self.assertEqual(clean[0]["annual_profit_multiple"], 1.0)

    def test_screening_never_turns_missing_data_into_a_pass(self):
        base = {"listing_id": "123", "title": "Acme", "asking_price": 12000, "monthly_profit": 1000, "annual_profit_multiple": 1.0, "age_months": 24, "monthly_traffic": 5000}
        self.assertEqual(screen_listing(base, {"max_price": 15000, "max_multiple": 1.5})["decision"], "manual_diligence")
        self.assertEqual(screen_listing(dict(base, monthly_profit=None), {})["decision"], "evidence_gap")
        self.assertEqual(screen_listing(base, {"max_price": 10000})["decision"], "excluded")
        self.assertIn("seller_claims_not_independently_verified", screen_listing(base, {})["flags"])

    def test_csv_diff_and_outputs(self):
        self.assertEqual(csv_cell("=HYPERLINK()"), "'=HYPERLINK()")
        payload = {"criteria": {"max_price": 20000}, "rows": [{"listing_id": "123", "title": "Acme SaaS", "asking_price": "$12k", "monthly_profit": "$1k", "age_months": 24, "monthly_traffic": 5000, "category": "SaaS", "source_url": "https://flippa.com/123-acme", "captured_at": "2026-11-09"}], "markets": [{"category": "SaaS", "displayed_listing_count": 677, "source_url": "https://flippa.com/buy/saas", "captured_at": "2026-11-09"}]}
        first = analyze(payload)
        changed = dict(payload)
        changed["rows"] = [dict(payload["rows"][0], asking_price="$13k", captured_at="2026-11-10")]
        second = analyze(changed, first["snapshot"])
        self.assertEqual(second["rows"][0]["status"], "changed")
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(second, tmp)
            self.assertTrue((Path(tmp) / "listings.csv").is_file())
            self.assertIn("not independently verified", (Path(tmp) / "report.md").read_text().lower())
            self.assertTrue((Path(tmp) / "run.json").is_file())

    def test_sanitized_live_category_context_is_not_a_deal(self):
        fixture = json.loads((Path(__file__).parent / "fixtures" / "sanitized_live.json").read_text())
        result = analyze({"rows": [], "markets": fixture["markets"]})
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["markets"][0]["displayed_listing_count"], 677)
        self.assertIn("not demand", result["report"])


if __name__ == "__main__":
    unittest.main()
