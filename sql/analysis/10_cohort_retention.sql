-- Monthly acquisition cohorts: % of each cohort purchasing again in month N
-- after their first order (month 0 = acquisition month, always 100%).
WITH cust_months AS (
    SELECT DISTINCT
        c.customer_id,
        c.cohort_month,
        (CAST(substr(o.order_month, 1, 4) AS INT) * 12 + CAST(substr(o.order_month, 6, 2) AS INT))
      - (CAST(substr(c.cohort_month, 1, 4) AS INT) * 12 + CAST(substr(c.cohort_month, 6, 2) AS INT))
            AS months_since_first
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id AND o.is_refunded = 0
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS cohort_customers FROM customers GROUP BY cohort_month
)
SELECT cm.cohort_month,
       cs.cohort_customers,
       cm.months_since_first,
       COUNT(DISTINCT cm.customer_id)                                      AS active_customers,
       ROUND(100.0 * COUNT(DISTINCT cm.customer_id) / cs.cohort_customers, 1) AS retention_pct
FROM cust_months cm
JOIN cohort_size cs ON cs.cohort_month = cm.cohort_month
GROUP BY cm.cohort_month, cm.months_since_first
ORDER BY cm.cohort_month, cm.months_since_first;
