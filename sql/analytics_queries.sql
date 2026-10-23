-- E-Commerce Sales & Revenue Analytics
-- Dialect: standard SQL (Athena / Redshift / BigQuery style).
-- Source table: orders (one row per order; the silver layer)
-- Columns: order_id, order_date, customer_id, customer_segment, region,
--          category, product, sales_channel, quantity, unit_price,
--          unit_cost, discount_pct, revenue, profit

-- 1. Monthly revenue, orders, AOV and month-over-month growth
SELECT DATE_TRUNC('month', order_date) AS month,
       COUNT(*) AS orders,
       SUM(revenue) AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2) AS aov,
       ROUND(100.0 * (SUM(revenue) - LAG(SUM(revenue)) OVER (ORDER BY DATE_TRUNC('month', order_date)))
             / LAG(SUM(revenue)) OVER (ORDER BY DATE_TRUNC('month', order_date)), 2) AS mom_revenue_pct
FROM orders GROUP BY 1 ORDER BY 1;

-- 2. Revenue and margin by category
SELECT category, COUNT(*) AS orders, SUM(revenue) AS revenue,
       SUM(profit) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2) AS margin_pct,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM orders GROUP BY 1 ORDER BY revenue DESC;

-- 3. Revenue by region
SELECT region, COUNT(*) AS orders, SUM(revenue) AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM orders GROUP BY 1 ORDER BY revenue DESC;

-- 4. Category monthly trend (feed for the category trend chart)
SELECT category, DATE_TRUNC('month', order_date) AS month,
       COUNT(*) AS orders, SUM(revenue) AS revenue
FROM orders GROUP BY 1, 2 ORDER BY 1, 2;

-- 5. Declining category detection: last 6 months vs prior 6 months
--    (windows anchored to the dataset's own max month)
WITH bounds AS (
  SELECT DATE_TRUNC('month', MAX(order_date)) AS last_month FROM orders
)
SELECT category,
       SUM(CASE WHEN order_date >  DATEADD(month, -6,  last_month) THEN revenue ELSE 0 END) AS revenue_last6,
       SUM(CASE WHEN order_date <= DATEADD(month, -6,  last_month)
                 AND order_date >  DATEADD(month, -12, last_month) THEN revenue ELSE 0 END) AS revenue_prior6,
       ROUND(100.0 * (SUM(CASE WHEN order_date > DATEADD(month, -6, last_month) THEN revenue ELSE 0 END)
             - SUM(CASE WHEN order_date <= DATEADD(month, -6, last_month)
                        AND order_date > DATEADD(month, -12, last_month) THEN revenue ELSE 0 END))
             / SUM(CASE WHEN order_date <= DATEADD(month, -6, last_month)
                        AND order_date > DATEADD(month, -12, last_month) THEN revenue ELSE 0 END), 2)
           AS change_pct
FROM orders, bounds GROUP BY 1 ORDER BY change_pct;

-- 6. Profit margin by product (most to least profitable)
SELECT product, category, COUNT(*) AS orders, SUM(quantity) AS units,
       SUM(revenue) AS revenue, SUM(profit) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2) AS margin_pct,
       ROUND(100.0 * AVG(discount_pct), 1) AS avg_discount_pct
FROM orders GROUP BY 1, 2 ORDER BY margin_pct DESC;

-- 7. Negative-margin products (products losing money overall)
SELECT product, category, SUM(revenue) AS revenue, SUM(profit) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2) AS margin_pct
FROM orders GROUP BY 1, 2
HAVING SUM(profit) < 0
ORDER BY profit;

-- 8. Discount band vs profitability (the discount tradeoff)
SELECT CASE
         WHEN discount_pct = 0 THEN '0%'
         WHEN discount_pct <= 0.10 THEN '1-10%'
         WHEN discount_pct <= 0.20 THEN '11-20%'
         WHEN discount_pct <= 0.30 THEN '21-30%'
         ELSE '>30%' END AS discount_band,
       COUNT(*) AS orders, SUM(revenue) AS revenue, SUM(profit) AS profit,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2) AS margin_pct
FROM orders GROUP BY 1 ORDER BY MIN(discount_pct);

-- 9. Top 20 customers by revenue
SELECT customer_id, customer_segment, region, COUNT(*) AS orders,
       SUM(revenue) AS revenue, SUM(profit) AS profit
FROM orders GROUP BY 1, 2, 3 ORDER BY revenue DESC LIMIT 20;

-- 10. Repeat purchase rate
SELECT COUNT(*) AS customers,
       SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repeat_customers,
       ROUND(100.0 * SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS repeat_rate_pct
FROM (SELECT customer_id, COUNT(*) AS order_count FROM orders GROUP BY 1) t;

-- 11. Customer value tiers (spend quartiles, RFM-lite monetary view)
WITH cust AS (
  SELECT customer_id, COUNT(*) AS orders, SUM(revenue) AS revenue,
         MAX(order_date) AS last_order
  FROM orders GROUP BY 1
), tiered AS (
  SELECT *, NTILE(4) OVER (ORDER BY revenue) AS quartile FROM cust
)
SELECT CASE quartile WHEN 4 THEN 'Platinum' WHEN 3 THEN 'Gold'
              WHEN 2 THEN 'Silver' ELSE 'Bronze' END AS tier,
       COUNT(*) AS customers, SUM(revenue) AS revenue,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct,
       ROUND(AVG(orders), 2) AS avg_orders
FROM tiered GROUP BY 1 ORDER BY quartile DESC;

-- 12. Revenue by customer segment with AOV
SELECT customer_segment, COUNT(DISTINCT customer_id) AS customers,
       COUNT(*) AS orders, SUM(revenue) AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2) AS aov,
       ROUND(100.0 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 2) AS revenue_share_pct
FROM orders GROUP BY 1 ORDER BY revenue DESC;

-- 13. Revenue by sales channel
SELECT sales_channel, COUNT(*) AS orders, SUM(revenue) AS revenue,
       ROUND(SUM(revenue) / COUNT(*), 2) AS aov,
       ROUND(100.0 * SUM(profit) / SUM(revenue), 2) AS margin_pct
FROM orders GROUP BY 1 ORDER BY revenue DESC;
