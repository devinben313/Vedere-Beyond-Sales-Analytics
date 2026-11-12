-- Revenue split by first vs repeat orders and by discount code usage.
SELECT
    CASE WHEN is_first_order = 1 THEN 'First order' ELSE 'Repeat order' END AS order_type,
    COALESCE(NULLIF(discount_code, ''), '(none)')                           AS discount_code,
    COUNT(*)                                                                AS orders,
    ROUND(SUM(net_sales), 2)                                                AS net_revenue,
    ROUND(AVG(net_sales), 2)                                                AS aov,
    ROUND(SUM(discount), 2)                                                 AS discount_given,
    ROUND(100.0 * SUM(contribution_margin) / SUM(net_sales), 1)             AS contribution_margin_pct
FROM orders
WHERE is_refunded = 0
GROUP BY 1, 2
ORDER BY 1, net_revenue DESC;
