# Fixed Income Portfolio Monitor
### A Python-based portfolio surveillance and compliance tool built to simulate real-world fixed income risk monitoring workflows

---

## What It Does

This tool builds a multi-sector fixed income portfolio, calculates key risk and performance metrics at both the position and portfolio level, and runs automated compliance checks against a defined mandate — flagging breaches and providing a full visual dashboard for reporting.

---

## Why I Built It

Fixed income portfolio management teams spend significant time on exactly two things: monitoring whether portfolios are performing within mandate constraints, and surfacing data issues before they distort risk metrics. Both tasks are traditionally manual, error-prone, and time-consuming at scale.

I built this tool to understand how surveillance workflow functions under the hood. The goal was to move beyond academic knowledge of fixed income concepts and build something that reflects how an actual analyst seat operates: ingesting portfolio data, computing risk exposure, checking compliance rules, and producing clean reporting output without manual intervention.

---

## Tools & Libraries

| Tool | Purpose |
|---|---|
| `Python 3` | Core language |
| `Pandas` | Portfolio data structuring and aggregation |
| `NumPy` | Bond pricing and duration calculations |
| `Matplotlib` | 8-panel visual dashboard and reporting output |
| `Jupyter Notebook` | Interactive development and presentation layer |

No external APIs or live data feeds — the tool runs entirely on structured input data

---

## How It Works

The project is structured across three modules that build on each other:

**Module 1 — Portfolio Construction**
Defines a five-bond portfolio across Government, Financial, Technology, and Municipal sectors. Computes present-value-based pricing for each position using coupon cash flows discounted at YTM, then calculates market value and portfolio weight per bond.

**Module 2 — Risk & Performance Engine**
Calculates Macaulay Duration, Modified Duration, and DV01 at the position level and then aggregates them to weighted portfolio-level metrics. Also produces sector concentration and credit quality breakdowns.

**Module 3 — Surveillance & Compliance Flagging**
Runs 17 automated checks against a defined mandate (Investment Policy Statement constraints), flags any breach with the specific metric, threshold, and deviation, and produces a structured pass/fail surveillance report.

---

## Key Outputs & Findings

> *Portfolio latest updated as of 2026-02-19 | Total Market Value: $32.47M*

| Metric | Value |
|---|---|
| Weighted Average YTM | 4.341% |
| Portfolio Modified Duration | 4.52 years |
| Portfolio DV01 | $14,679 |
| AAA / AA Allocation | 84.91% |
| Compliance Checks Run | 17 |
| Breaches Detected | 1 |

**Breach Detected — Government Sector Concentration**
The surveillance engine flagged a Government sector allocation of 55.00% against a 50% mandate limit. In a live portfolio context, this breach would trigger a rebalancing review with the portfolio manager and require documented escalation to compliance — exactly the workflow this tool is designed to surface automatically.

**Key Risk Insight — UST-10Y Duration Concentration**
Despite representing 24% of the portfolio by market value, the 10-year Treasury position contributed 39% of total portfolio DV01 ($5,793 of $14,679). This hidden rate sensitivity concentration is the kind of finding that manual monitoring frequently misses.

---

## Dashboard Output

The tool generates an 8-panel visual dashboard saved automatically as `portfolio_monitor_dashboard.png`:

- Portfolio KPI Scorecard
- Surveillance Status (pass/breach summary)
- Sector Allocation (pie)
- Credit Quality Breakdown vs. floor limit
- Modified Duration by Position
- DV01 by Position vs. mandate limit
- Sector Concentration vs. limit (breach highlighted in red)
- Market Value by Position

<img width="2205" height="1922" alt="portfolio_monitor_dashboard" src="https://github.com/user-attachments/assets/c21b9757-8d08-46fe-8582-4ba3f93a38bf" />


---

## Skills Demonstrated

- Fixed income pricing and risk analytics (duration, DV01, YTM)
- Portfolio surveillance and compliance monitoring logic
- Automated reporting workflow design
- Data structuring and aggregation with Pandas
- Financial data visualization with Matplotlib
