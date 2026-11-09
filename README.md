# Flippa Deal Screener | Powered by Bright Data

> **A listing can look cheap for two reasons: a bargain, or missing numbers. Find out which before you spend a dollar.**

Turn selected public Flippa listing pages into a disciplined acquisition research queue. Calculate simple annual profit multiples when the figures allow it. Flag missing price, profit, age, and traffic. Keep seller claims separate from verified facts.

## The decision

**Which listing deserves manual diligence, which is outside your rules, and which lacks evidence?**

Use it to:

- Screen a buyer-supplied set of SaaS, content, ecommerce, or app listings.
- Compare displayed price and monthly profit without hiding missing inputs.
- Compare current rows with a prior snapshot for price or profit changes; vanished listings are not labeled as removed.

## Why Bright Data

Deal research should not require a new scraper for every marketplace. [Bright Data](https://brightdata.com/) MCP gives your agent one way to attempt public category and user-supplied listing pages as Markdown inside the research workflow. The live check verified category-page context only; it did not verify an individual listing capture. The agent can spend its effort on diligence questions instead of page plumbing, while failed listing captures remain explicit evidence gaps.

## Start with 5,000 free credits

**New Bright Data accounts include 5,000 free credits per month. No credit card is required.** Credits share one account-level pool, reset monthly, and are subject to current eligibility and product terms.

The default plan uses **1 category page and up to 8 user-supplied listing pages**, with at most **2 retries**. That is 9 planned requests before retries. Category pages provide context; they are not represented as a complete listing inventory.

## What you get

- `report.md`: a concise manual-diligence queue and displayed category context.
- `listings.csv`: stable `listing_id` keys, economics, gaps, and change status.
- `run.json`: a watchlist snapshot for the next review.
- Explicit decisions: `manual_diligence`, `evidence_gap`, or `excluded`.

## Give this to your agent

```text
Use flippa-deal-screener for these public Flippa listing URLs: [URLs].
My maximum price is [amount]. My minimum monthly profit is [amount].
My optional maximum annual profit multiple is [number].
Add [optional public Flippa category URL] for displayed category context.

Use Bright Data MCP to fetch at most 1 category page and 8 listing pages.
Show the 9-request plan first. Retry at most twice overall. Do not claim to
enumerate category results if the capture is truncated before listing cards.
Use listing URLs I supplied or direct public listing links actually present in
the capture. Do not invent listing details or bypass login.

Strip seller and broker identities. Preserve displayed figures as source claims.
Normalize the evidence and run scripts/report.py. Return the diligence queue,
missing-evidence flags, and changed rows. Do not value a business, contact a seller,
place a bid, or make a purchase recommendation.
```

## Install

Requires Python 3.10+, an agent with Bright Data MCP connected as `brightdata`, and access to this private repo.

```bash
git clone git@github.com:yaronbeen/flippa-deal-screener-powered-by-bright-data.git \
  ~/.claude/skills/flippa-deal-screener
```

For OpenCode, clone into `~/.config/opencode/skills/flippa-deal-screener`. See the [connection and schema guide](docs/technical-guide.md).

## Run the example

```bash
cd ~/.claude/skills/flippa-deal-screener
python3 scripts/report.py examples/input.json --output-dir examples/output
```

For a later watchlist review:

```bash
python3 scripts/report.py new-input.json \
  --previous examples/output/run.json --output-dir output
```

The example is synthetic. The [live-check note](docs/live-check.md) documents the category capture and its truncation limit.

## Example output

| Listing | Price | Monthly profit | Annual multiple | Decision | Flags | Status |
|---|---:|---:|---:|---|---|---|
| Acme Metrics | 24000.0 | 2000.0 | 1.0 | manual_diligence | seller_claims_not_independently_verified | new |
| Beta Content | 18000.0 | unknown | unknown | evidence_gap | seller_claims_not_independently_verified, profit_not_disclosed | new |
| Gamma Commerce | 60000.0 | 3000.0 | 1.67 | excluded | seller_claims_not_independently_verified | new |

`manual_diligence` means the supplied fields passed your mechanical rules. It does not mean the business is good, the seller is right, or the price is fair.

## Tests

The tests were committed before the helper.

```bash
python3 -m unittest discover -s tests -v
```

Tests cover money parsing, positive-profit gates, dedupe, seller-identity removal, missing-evidence decisions, buyer filters, CSV injection, watchlist diffs, and a sanitized live category capture. See [the testing note](docs/testing.md).

## What this is not

- Not a valuation, fairness opinion, or investment recommendation.
- Not independent verification of revenue, profit, traffic, ownership, or seller claims.
- Not a complete marketplace scrape. You supply the deal set.
- Not a bidding, broker-contact, or transaction tool.
- Not permission to ignore Flippa's current terms. Review them before collection.

## Repo map

```text
SKILL.md                 Agent workflow and MCP limits
scripts/report.py        Stdlib-only deterministic helper
tests/                   Unit tests + sanitized live fixture
examples/                Synthetic input and generated output
docs/                    Setup, schema, testing, and live-check notes
```

## FAQ

**Why not discover every listing from a category page?**  The tested capture was cut at 40,000 characters before listing cards. This repo tells the truth and uses your selected listing URLs instead.

**What is the CSV key?**  `listing_id`, taken from the public listing URL. Capture timestamps do not count as content changes.

**Was an individual listing page verified live?**  No. The smoke check fetched only the home and category pages, and the category capture ended before listing cards. Listing-level collection remains an explicit runtime evidence check, not a verified claim.

**What happens when monthly profit is missing?**  The multiple stays unknown and the listing becomes `evidence_gap`. Zero is never substituted for unknown. Missing age or traffic adds a flag but does not block `manual_diligence` when explicit price and positive monthly profit pass your rules.

---

Built by Yaron Been. MIT licensed. Powered by Bright Data, without implying endorsement.
