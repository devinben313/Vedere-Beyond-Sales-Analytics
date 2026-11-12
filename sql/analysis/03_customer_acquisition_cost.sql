-- Customer acquisition cost (CAC) by month.
--   paid CAC    = Meta spend / customers acquired through a Meta campaign
--   blended CAC = Meta spend / all new customers (any channel)
WITH new_cust AS (
    SELECT cohort_month AS month,
           COUNT(*) AS new_customers,
           SUM(CASE WHEN acquisition_channel = 'Meta Ads' THEN 1 ELSE 0 END) AS meta_new_customers
    FROM customers GROUP BY cohort_month
),
spend AS (
    SELECT strftime('%Y-%m', date) AS month, SUM(spend) AS ad_spend
    FROM ad_performance_daily GROUP BY 1
)
SELECT n.month,
       ROUND(s.ad_spend, 2)                                         AS ad_spend,
       n.new_customers,
       n.meta_new_customers,
       ROUND(s.ad_spend / NULLIF(n.meta_new_customers, 0), 2)       AS paid_cac,
       ROUND(s.ad_spend / NULLIF(n.new_customers, 0), 2)            AS blended_cac,
       ROUND(100.0 * n.meta_new_customers / n.new_customers, 1)     AS pct_new_from_meta
FROM new_cust n LEFT JOIN spend s ON s.month = n.month
ORDER BY n.month;
