-- Category-level profitability and share of revenue.
SELECT
    category,
    COUNT(DISTINCT product_id)                                       AS skus,
    SUM(quantity)                                                    AS units_sold,
    ROUND(SUM(net_line_revenue), 2)                                  AS net_revenue,
    ROUND(SUM(net_line_revenue - line_cogs), 2)                      AS gross_profit,
    ROUND(100.0 * SUM(net_line_revenue - line_cogs) / SUM(net_line_revenue), 1) AS margin_pct,
    ROUND(SUM(net_line_revenue) / SUM(quantity), 2)                  AS avg_net_price,
    ROUND(100.0 * SUM(net_line_revenue) / SUM(SUM(net_line_revenue)) OVER (), 1) AS pct_of_revenue
FROM v_order_lines
GROUP BY category
ORDER BY gross_profit DESC;
