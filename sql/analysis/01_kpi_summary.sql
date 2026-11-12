-- Headline KPIs for the full 14-month period.
WITH s AS (
    SELECT SUM(net_sales)              AS net_revenue,
           SUM(gross_sales)            AS gross_sales,
           SUM(discount)               AS discounts,
           SUM(net_sales - cogs)       AS gross_profit,
           SUM(contribution_margin)    AS contribution_margin,
           COUNT(*)                    AS orders,
           SUM(units)                  AS units,
           SUM(CASE WHEN campaign_id IS NOT NULL THEN net_sales END) AS meta_attributed_revenue
    FROM orders WHERE is_refunded = 0
),
a AS (SELECT SUM(spend) AS ad_spend, SUM(impressions) AS impressions FROM ad_performance_daily),
c AS (SELECT COUNT(*) AS customers,
             SUM(is_repeat_customer) AS repeat_customers,
             SUM(CASE WHEN acquisition_channel = 'Meta Ads' THEN 1 ELSE 0 END) AS meta_customers
      FROM customers)
SELECT
    MIN(o.order_date)                                       AS period_start,
    MAX(o.order_date)                                       AS period_end,
    ROUND(s.net_revenue, 2)                                 AS net_revenue,
    ROUND(s.gross_sales, 2)                                 AS gross_sales,
    ROUND(s.discounts, 2)                                   AS discounts,
    (SELECT ROUND(SUM(refund_amount), 2) FROM orders)       AS refunds,
    (SELECT COUNT(*) FROM orders WHERE is_refunded = 1)     AS refunded_orders,
    s.orders,
    s.units,
    c.customers                                             AS unique_customers,
    ROUND(s.net_revenue / s.orders, 2)                      AS avg_order_value,
    ROUND(1.0 * s.orders / c.customers, 2)                  AS orders_per_customer,
    ROUND(100.0 * c.repeat_customers / c.customers, 1)      AS repeat_purchase_rate_pct,
    ROUND(100.0 * s.gross_profit / s.net_revenue, 1)        AS gross_margin_pct,
    ROUND(s.contribution_margin, 2)                         AS contribution_margin,
    ROUND(a.ad_spend, 2)                                    AS meta_ad_spend,
    ROUND(s.meta_attributed_revenue, 2)                     AS meta_attributed_revenue,
    ROUND(s.meta_attributed_revenue / a.ad_spend, 2)        AS meta_roas,
    ROUND(s.net_revenue / a.ad_spend, 2)                    AS blended_mer,
    ROUND(a.ad_spend / c.meta_customers, 2)                 AS paid_cac,
    ROUND(a.ad_spend / c.customers, 2)                      AS blended_cac,
    ROUND(s.contribution_margin - a.ad_spend, 2)            AS profit_after_ad_spend
FROM s, a, c, orders o;
