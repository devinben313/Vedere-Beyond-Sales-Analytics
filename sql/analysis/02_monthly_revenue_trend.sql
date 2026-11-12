-- Monthly revenue, orders, new vs returning mix, ad spend and ROAS.
SELECT
    month,
    orders,
    new_customers,
    ROUND(net_revenue, 2)                                         AS net_revenue,
    ROUND(new_customer_revenue, 2)                                AS new_customer_revenue,
    ROUND(returning_customer_revenue, 2)                          AS returning_customer_revenue,
    ROUND(net_revenue / orders, 2)                                AS aov,
    ROUND(ad_spend, 2)                                            AS ad_spend,
    ROUND(meta_attributed_revenue, 2)                             AS meta_attributed_revenue,
    ROUND(meta_attributed_revenue / NULLIF(ad_spend, 0), 2)       AS meta_roas,
    ROUND(100.0 * (net_revenue - gross_profit) / net_revenue, 1)  AS cogs_pct,
    ROUND(profit_after_ads, 2)                                    AS profit_after_ads,
    ROUND(SUM(net_revenue) OVER (ORDER BY month), 2)              AS cumulative_revenue,
    ROUND(100.0 * (net_revenue - LAG(net_revenue) OVER (ORDER BY month))
          / LAG(net_revenue) OVER (ORDER BY month), 1)            AS mom_growth_pct
FROM v_monthly_kpis
ORDER BY month;
