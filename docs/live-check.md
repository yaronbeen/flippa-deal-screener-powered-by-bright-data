# Flippa Live Check | Powered by Bright Data

Checked 2026-11-09 with Bright Data MCP `scrape_as_markdown`.

## What worked

- `https://flippa.com/` returned public marketplace navigation and category links.
- `https://flippa.com/buy/saas` returned public category and filter content.
- The SaaS page displayed category labels including SaaS `677`, Ecommerce `2,305`, and Content `789` at capture time. These are displayed listing labels, not transactions or demand.

The three category observations are preserved in the sanitized live fixture.

## The limit that shaped the skill

The SaaS category response reported 97,572 characters and returned the first 40,000. The capture ended in filters before individual listing cards. No listing-level live fixture is claimed.

Accordingly, this skill requires user-supplied public listing URLs for deal detail. It never claims that a truncated category page enumerated the marketplace. A listing that lacks price, profit, age, or traffic becomes `evidence_gap`.

Review Flippa's current terms before collection. No login, seller contact, bid, or purchase is part of the smoke check or the skill.
