-- ROAS rolled up by campaign strategy and by creative format.
SELECT 'strategy' AS dimension, strategy AS value,
       COUNT(*) AS campaigns,
       ROUND(SUM(spend), 2) AS spend,
       ROUND(SUM(purchase_value), 2) AS attributed_revenue,
       ROUND(SUM(purchase_value) / SUM(spend), 2) AS roas,
       ROUND(SUM(spend) / NULLIF(SUM(purchases), 0), 2) AS cost_per_purchase,
       ROUND(SUM(contribution_margin) - SUM(spend), 2) AS profit_after_ad_spend
FROM v_campaign_performance GROUP BY strategy
UNION ALL
SELECT 'creative_type', creative_type,
       COUNT(*),
       ROUND(SUM(spend), 2),
       ROUND(SUM(purchase_value), 2),
       ROUND(SUM(purchase_value) / SUM(spend), 2),
       ROUND(SUM(spend) / NULLIF(SUM(purchases), 0), 2),
       ROUND(SUM(contribution_margin) - SUM(spend), 2)
FROM v_campaign_performance GROUP BY creative_type
ORDER BY dimension DESC, roas DESC;
