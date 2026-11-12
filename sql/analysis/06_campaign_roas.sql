-- Meta campaign scorecard: ROAS, CPA, funnel rates and profit after ad spend.
SELECT
    campaign_id,
    campaign_name,
    strategy,
    creative_type,
    start_date,
    end_date,
    ROUND(spend, 2)                                            AS spend,
    impressions,
    ROUND(1000.0 * spend / impressions, 2)                     AS cpm,
    ROUND(100.0 * link_clicks / impressions, 2)                AS link_ctr_pct,
    ROUND(spend / NULLIF(link_clicks, 0), 2)                   AS cpc,
    ROUND(100.0 * purchases / NULLIF(landing_page_views, 0), 2) AS lpv_to_purchase_pct,
    purchases,
    new_customers,
    ROUND(purchase_value, 2)                                   AS attributed_revenue,
    ROUND(purchase_value / spend, 2)                           AS roas,
    ROUND(spend / NULLIF(purchases, 0), 2)                     AS cost_per_purchase,
    ROUND(spend / NULLIF(new_customers, 0), 2)                 AS cost_per_new_customer,
    ROUND(contribution_margin - spend, 2)                      AS profit_after_ad_spend,
    ROUND(100.0 * spend / SUM(spend) OVER (), 1)               AS pct_of_spend,
    ROUND(100.0 * purchase_value / SUM(purchase_value) OVER (), 1) AS pct_of_attributed_revenue,
    RANK() OVER (ORDER BY purchase_value / spend DESC)         AS roas_rank
FROM v_campaign_performance
ORDER BY roas DESC;
