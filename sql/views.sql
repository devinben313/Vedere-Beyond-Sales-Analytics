-- =====================================================================
-- Reusable analytical views
-- =====================================================================

-- One row per non-refunded order line, with discount allocated pro-rata
-- so product-level revenue reconciles to order net sales.
CREATE VIEW v_order_lines AS
SELECT
    oi.order_item_id,
    o.order_id,
    o.order_date,
    o.order_month,
    o.customer_id,
    o.is_first_order,
    o.attribution_channel,
    o.campaign_id,
    p.product_id,
    p.product_name,
    p.category,
    p.collection,
    oi.size,
    oi.quantity,
    oi.unit_price,
    oi.line_revenue                                            AS gross_line_revenue,
    oi.line_revenue * (1 - o.discount / o.gross_sales)         AS net_line_revenue,
    oi.line_cogs
FROM order_items oi
JOIN orders   o ON o.order_id  = oi.order_id
JOIN products p ON p.product_id = oi.product_id
WHERE o.is_refunded = 0;

-- Campaign totals: Meta delivery metrics + Shopify-side outcomes.
CREATE VIEW v_campaign_performance AS
WITH delivery AS (
    SELECT campaign_id,
           SUM(spend) AS spend, SUM(impressions) AS impressions, SUM(clicks) AS clicks,
           SUM(link_clicks) AS link_clicks, SUM(landing_page_views) AS landing_page_views,
           SUM(add_to_cart) AS add_to_cart, SUM(purchases) AS purchases,
           SUM(purchase_value) AS purchase_value
    FROM ad_performance_daily
    GROUP BY campaign_id
),
outcomes AS (
    SELECT campaign_id,
           SUM(is_first_order)                      AS new_customers,
           SUM(contribution_margin)                 AS contribution_margin
    FROM orders
    WHERE is_refunded = 0 AND campaign_id IS NOT NULL
    GROUP BY campaign_id
)
SELECT c.campaign_id, c.campaign_name, c.strategy, c.objective, c.creative_type, c.funnel_stage,
       c.start_date, c.end_date,
       d.spend, d.impressions, d.clicks, d.link_clicks, d.landing_page_views, d.add_to_cart,
       d.purchases, d.purchase_value,
       COALESCE(o.new_customers, 0)       AS new_customers,
       COALESCE(o.contribution_margin, 0) AS contribution_margin
FROM ad_campaigns c
JOIN delivery d      ON d.campaign_id = c.campaign_id
LEFT JOIN outcomes o ON o.campaign_id = c.campaign_id;

-- Monthly business KPIs.
CREATE VIEW v_monthly_kpis AS
WITH sales AS (
    SELECT order_month AS month,
           COUNT(*)                        AS orders,
           COUNT(DISTINCT customer_id)     AS active_customers,
           SUM(is_first_order)             AS new_customers,
           SUM(net_sales)                  AS net_revenue,
           SUM(CASE WHEN is_first_order = 1 THEN net_sales ELSE 0 END) AS new_customer_revenue,
           SUM(CASE WHEN is_first_order = 0 THEN net_sales ELSE 0 END) AS returning_customer_revenue,
           SUM(net_sales - cogs)           AS gross_profit,
           SUM(contribution_margin)        AS contribution_margin,
           SUM(CASE WHEN campaign_id IS NOT NULL THEN net_sales ELSE 0 END) AS meta_attributed_revenue
    FROM orders
    WHERE is_refunded = 0
    GROUP BY order_month
),
ads AS (
    SELECT strftime('%Y-%m', date) AS month, SUM(spend) AS ad_spend
    FROM ad_performance_daily GROUP BY 1
)
SELECT s.*, COALESCE(a.ad_spend, 0) AS ad_spend,
       s.contribution_margin - COALESCE(a.ad_spend, 0) AS profit_after_ads
FROM sales s LEFT JOIN ads a ON a.month = s.month;
