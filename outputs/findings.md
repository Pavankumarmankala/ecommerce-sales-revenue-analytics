# Findings — E-Commerce Sales & Revenue Analytics

Dataset: 50,906 orders, 11,133 customers, 24 months (Jan 2024 – Dec 2025). Total revenue $8,291,093.42, total profit $2,035,059.90 (24.55% margin), AOV $162.87.

## 1. Revenue trend
- Revenue grew from $286,339 in the first month to $456,709 in the last month; peak month was 2025-12 at $456,709 (holiday seasonality).
- Steepest category decline: **Home & Kitchen**, down **36.81%** comparing average monthly revenue in the last 6 months ($49,920) vs the prior 6 months ($79,001). This matches planted pattern #1.

## 2. Product profitability
- Most profitable: **Plush Toy** at 52.42% margin. Least profitable: **Fitness Tracker** at -14.37%.
- 3 products have negative overall margins; together they lost $122,383. All are heavy-discount promo products (planted pattern #3).
- Discount tradeoff: orders with no discount earn 33.07% margin; orders discounted >30% earn -29.72% — deep discounts destroy margin.

## 3. Customers & regions
- Premium customers are 8.55% of customers but drive 37.12% of revenue (AOV $229) — planted pattern #4, verified.
- Top value tier (Platinum, top spend quartile) accounts for 63.45% of revenue. Repeat rate: 85.47% of customers ordered 2+ times.
- Fastest-growing region: **West**, revenue up 77.43% (avg monthly, first 6 vs last 6 months) — planted pattern #2, verified.

## 4. Revenue opportunities (each tied to a computed number)
1. **Cap discounts at 20% on negative-margin promo products (Hair Dryer, Mechanical Keyboard, Fitness Tracker)** — These products lost $122,383 over 24 months at current 35-55% promo discounts. Computed impact: **$249,168** (profit recoverable over 24 months if discount capped at 20%, same volumes).
2. **Reverse the Home & Kitchen decline (-36.81% last 6 vs prior 6 months)** — Average monthly revenue fell from $79,001 to $49,920. Computed impact: **$348,977** (annual revenue recoverable at the prior-6-month run rate).
3. **Lift Occasional-segment basket size toward the Regular-segment AOV (bundles, free-shipping threshold, second-item offers)** — Occasional AOV is $113.81 vs Regular $145.63 across 7,616 Occasional orders. Computed impact: **$242,341** (revenue upside over 24 months if Occasional AOV matched Regular AOV).
