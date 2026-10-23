# E-Commerce Sales & Revenue Analytics

End-to-end data analyst project: 24 months of e-commerce orders are
analysed in Python (pandas) and SQL to answer the questions a sales
leadership team actually asks — where is revenue declining, which
products make or lose money, what do discounts really cost, and which
customers and regions drive growth — with every finding computed from
the data and each recommendation tied to a dollar figure.

## Verified results (actual run, seed = 42)

| Metric | Value |
|---|---|
| Orders analysed | 50,906 |
| Customers / months covered | 11,133 / 24 (Jan 2024 – Dec 2025) |
| Total revenue / profit | $8,291,093.42 / $2,035,059.90 |
| Overall margin / AOV | 24.55% / $162.87 |
| Declining category detected | Home & Kitchen, **-36.81%** (avg monthly revenue $79,001 -> $49,920, last 6 vs prior 6 months) |
| Most / least profitable product | Plush Toy (+52.42% margin) / Fitness Tracker (-14.37%) |
| Negative-margin products | 3 (Fitness Tracker, Mechanical Keyboard, Hair Dryer), losing $122,382.58 combined |
| Discount tradeoff | Margin falls 33.07% (no discount) -> 27.86% -> 19.22% -> 10.26% -> **-29.72%** (>30% discount) |
| Fastest-growing region | West, +77.43% (avg monthly revenue, first 6 vs last 6 months) |
| Premium segment | 8.55% of customers -> 37.12% of revenue (AOV $228.96) |
| Top value tier (Platinum quartile) | 63.45% of revenue |
| Repeat customer rate | 85.47% |

Full findings, including 3 quantified revenue opportunities
($249,168 profit recoverable by capping promo discounts at 20%;
$348,977 annual revenue from reversing the Home & Kitchen decline;
$242,341 from lifting Occasional-segment AOV to the Regular level):
`outputs/findings.md`. All numbers: `outputs/metrics.json`.
Charts + HTML dashboard: `outputs/`.

## Dataset — planted patterns, verified by the analysis
The seeded generator (`src/generate_orders.py`, seed = 42) builds
~51k orders for 24 products in 6 categories, 4 regions and 3 customer
segments, with 4 patterns planted on purpose. The analysis code never
reads the planted labels — it detects each pattern from the data, and
the pytest suite asserts the detections match the plants:

1. **Declining category** — "Home & Kitchen" order weight decays
   (multiplier 0.78 -> 0.28) over the last 6 months. Detected as the
   steepest last-6 vs prior-6 revenue decline: -36.81%.
2. **Growing region** — "West" customers are sampled up to 1.9x by
   month 24. Detected as the fastest-growing region: +77.43%.
3. **Discount-driven losses** — Fitness Tracker, Mechanical Keyboard
   and Hair Dryer (28-30% base margins) are discounted 35-55% on ~80%
   of orders. They are exactly the 3 products detected with negative
   overall margins, and the >30% discount band earns -29.72% margin.
4. **High-value segment** — "Premium" customers (~8% of the base)
   order ~3.2x as often with larger baskets. Detected: 8.55% of
   customers producing 37.12% of revenue.

Definitions: revenue = quantity x unit_price x (1 - discount);
profit = revenue - quantity x unit_cost (discounts come out of the
seller's margin, as in real retail).

## Run it
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python run_pipeline.py     # generates, analyses, dashboards
.venv/bin/python -m pytest tests/    # 7 tests incl. planted-pattern detection
```

## Layout
- `src/generate_orders.py` — seeded synthetic orders + the 4 planted patterns, documented in code
- `src/analysis.py` — monthly/category trends + decline detector, product profitability, discount bands, region growth, segments, customer value tiers, quantified opportunities
- `src/pipeline.py` — bronze (raw Parquet) -> silver (cleaned orders) -> gold aggregates, writes `outputs/metrics.json` and `outputs/findings.md`
- `src/dashboard.py` — 5 charts (monthly revenue, category trend with decline highlighted, product margin, discount band vs margin, region growth) + HTML dashboard
- `sql/analytics_queries.sql` — 13 queries (monthly revenue + MoM, category/region revenue, decline detection, margin by product, negative-margin products, discount bands, top customers, repeat rate, value tiers, segments, channels)
- `powerbi/` — 3-page dashboard spec (Executive Overview, Product & Profitability, Customer Insights) + DAX measures

## Resume bullets (verified — safe to use)
**E-Commerce Sales & Revenue Analytics (Python + SQL + Power BI)**
- Analysed 50,906 e-commerce orders ($8.29M revenue, 11,133 customers, 24 months) in Python (pandas) and SQL to diagnose sales performance, detecting a 36.8% revenue decline in the Home & Kitchen category (average monthly revenue $79,001 → $49,920 over the last 6 months) and 77.4% revenue growth in the West region, and presenting trends in a Power BI dashboard spec with DAX measures for revenue, margin, AOV and MoM growth.
- Quantified the discount-profitability tradeoff across 24 products — margin falls from 33.1% on undiscounted orders to -29.7% on orders discounted over 30% — isolating 3 negative-margin products that lost $122,383, and modelled $249,168 in recoverable profit from capping their discounts at 20%.
- Segmented customers by value (spend quartiles and RFM-style tiers), finding Premium customers are 8.6% of the customer base but drive 37.1% of revenue (AOV $228.96 vs $162.87 overall) and the top spend quartile accounts for 63.5% of revenue, informing retention and basket-size recommendations worth a computed $242,341.
