-- Month x campaign spend and ROAS (feeds the ad performance trend view).
SELECT strftime('%Y-%m', a.date)                         AS month,
       a.campaign_id,
       c.campaign_name,
       c.strategy,
       ROUND(SUM(a.spend), 2)                            AS spend,
       SUM(a.purchases)                                  AS purchases,
       ROUND(SUM(a.purchase_value), 2)                   AS attributed_revenue,
       ROUND(SUM(a.purchase_value) / SUM(a.spend), 2)    AS roas
FROM ad_performance_daily a
JOIN ad_campaigns c ON c.campaign_id = a.campaign_id
GROUP BY 1, 2
ORDER BY 1, 2;
