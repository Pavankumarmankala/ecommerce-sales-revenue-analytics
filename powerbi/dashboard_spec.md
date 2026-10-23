# Power BI Dashboard — E-Commerce Sales & Revenue Analytics

Data source: gold layer CSVs in `data/gold/` (monthly_revenue,
category_monthly, category_summary, product_profitability,
discount_band_summary, region_summary, segment_summary,
customer_value_tiers, top_customers), or the silver `orders` table
directly. Model: orders fact linked to a calendar table on order_date;
category, region, segment and channel as slicer dimensions.

## Page 1 — Executive Sales Overview
- KPI cards: Total Revenue, Total Profit, Profit Margin %, Total Orders, AOV
- Line chart: monthly revenue with MoM growth (monthly_revenue)
- Bar chart: revenue by category, revenue by region
- Slicers: month, category, region, customer segment, sales channel

## Page 2 — Product & Profitability Diagnosis
- Barh chart: profit margin % by product, conditional formatting
  (red below 0% — the negative-margin promo products)
- Clustered bar: category average monthly revenue, last 6 vs prior 6 months,
  with the declining category called out
- Bar chart: average margin % by discount band (the discount tradeoff)
- Table: product profitability (orders, units, revenue, profit, margin %,
  avg discount %)

## Page 3 — Customer Insights
- Donut chart: revenue share by customer segment (Premium vs Regular
  vs Occasional) next to customer share, to show concentration
- Bar chart: revenue share by customer value tier (Platinum/Gold/
  Silver/Bronze)
- KPI cards: Repeat Rate %, Premium AOV, Platinum revenue share
- Table: top 20 customers by revenue
