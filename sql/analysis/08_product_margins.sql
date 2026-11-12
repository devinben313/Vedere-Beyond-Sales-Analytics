-- Product profitability: units, net revenue (after allocated discounts),
-- COGS, gross profit and margin, ranked by gross profit.
SELECT
    l.product_id,
    l.product_name,
    l.category,
    l.collection,
    p.retail_price,
    p.unit_cost,
    ROUND(100.0 * p.margin_pct, 1)                                   AS list_margin_pct,
    SUM(l.quantity)                                                  AS units_sold,
    COUNT(DISTINCT l.order_id)                                       AS orders,
    ROUND(SUM(l.net_line_revenue), 2)                                AS net_revenue,
    ROUND(SUM(l.line_cogs), 2)                                       AS cogs,
    ROUND(SUM(l.net_line_revenue - l.line_cogs), 2)                  AS gross_profit,
    ROUND(100.0 * SUM(l.net_line_revenue - l.line_cogs) / SUM(l.net_line_revenue), 1) AS realized_margin_pct,
    ROUND(100.0 * SUM(l.net_line_revenue) / SUM(SUM(l.net_line_revenue)) OVER (), 1)  AS pct_of_revenue,
    ROUND(SUM(l.net_line_revenue - l.line_cogs)
          / (julianday('2025-10-31') - julianday(p.launch_date) + 1) * 30, 2)     AS gross_profit_per_30_days_live,
    RANK() OVER (ORDER BY SUM(l.net_line_revenue - l.line_cogs) DESC)            AS profit_rank
FROM v_order_lines l
JOIN products p ON p.product_id = l.product_id
GROUP BY l.product_id
ORDER BY gross_profit DESC;
