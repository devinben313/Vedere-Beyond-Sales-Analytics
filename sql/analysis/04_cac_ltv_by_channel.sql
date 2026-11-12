-- Acquisition channel quality: customers, repeat rate, LTV and LTV:CAC.
-- Only Meta Ads has a direct media cost; organic channels show CAC = 0.
WITH spend AS (SELECT SUM(spend) AS total_spend FROM ad_performance_daily)
SELECT
    acquisition_channel,
    COUNT(*)                                                       AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)             AS pct_of_customers,
    ROUND(100.0 * AVG(is_repeat_customer), 1)                      AS repeat_rate_pct,
    ROUND(AVG(total_orders), 2)                                    AS avg_orders,
    ROUND(AVG(lifetime_revenue), 2)                                AS avg_ltv_revenue,
    ROUND(AVG(lifetime_contribution), 2)                           AS avg_ltv_contribution,
    ROUND(CASE WHEN acquisition_channel = 'Meta Ads'
               THEN (SELECT total_spend FROM spend) / COUNT(*) ELSE 0 END, 2) AS cac,
    ROUND(CASE WHEN acquisition_channel = 'Meta Ads'
               THEN AVG(lifetime_contribution) / ((SELECT total_spend FROM spend) / COUNT(*)) END, 2)
                                                                   AS ltv_to_cac
FROM customers
GROUP BY acquisition_channel
ORDER BY customers DESC;
