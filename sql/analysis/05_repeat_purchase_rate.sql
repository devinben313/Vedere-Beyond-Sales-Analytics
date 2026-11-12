-- Repeat purchase behaviour: distribution of orders per customer,
-- overall repeat rate and days between 1st and 2nd order.
WITH dist AS (
    SELECT CASE WHEN total_orders >= 4 THEN '4+' ELSE CAST(total_orders AS TEXT) END AS orders_bucket,
           COUNT(*) AS customers
    FROM customers
    WHERE total_orders > 0
    GROUP BY 1
),
second AS (
    SELECT o1.customer_id,
           julianday(o2.order_date) - julianday(o1.order_date) AS days_to_second
    FROM orders o1
    JOIN orders o2 ON o2.customer_id = o1.customer_id
                  AND o1.customer_order_number = 1 AND o2.customer_order_number = 2
)
SELECT d.orders_bucket,
       d.customers,
       ROUND(100.0 * d.customers / SUM(d.customers) OVER (), 1)         AS pct_customers,
       (SELECT ROUND(100.0 * AVG(is_repeat_customer), 1) FROM customers) AS overall_repeat_rate_pct,
       (SELECT ROUND(AVG(days_to_second), 0) FROM second)               AS avg_days_to_2nd_order,
       (SELECT COUNT(*) FROM second)                                    AS customers_with_2nd_order
FROM dist d
ORDER BY d.orders_bucket;
