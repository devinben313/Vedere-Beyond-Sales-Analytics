-- Cumulative repeat rate: share of customers who have placed a 2nd order
-- within N days of their first, counting only customers observed >= N days.
WITH firsts AS (
    SELECT c.customer_id,
           c.first_order_date,
           julianday('2025-10-31') - julianday(c.first_order_date) AS days_observed,
           (SELECT MIN(julianday(o.order_date)) - julianday(c.first_order_date)
            FROM orders o WHERE o.customer_id = c.customer_id AND o.customer_order_number = 2) AS days_to_second
    FROM customers c
),
windows(n) AS (VALUES (30), (60), (90), (120), (180), (270), (365))
SELECT w.n AS window_days,
       COUNT(*) AS eligible_customers,
       SUM(CASE WHEN f.days_to_second <= w.n THEN 1 ELSE 0 END) AS repurchased,
       ROUND(100.0 * SUM(CASE WHEN f.days_to_second <= w.n THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_rate_pct
FROM windows w
JOIN firsts f ON f.days_observed >= w.n
GROUP BY w.n
ORDER BY w.n;
