-- Which products does each campaign sell? (top 3 products per campaign by revenue)
WITH ranked AS (
    SELECT l.campaign_id, l.product_name,
           SUM(l.quantity) AS units,
           ROUND(SUM(l.net_line_revenue), 2) AS net_revenue,
           ROW_NUMBER() OVER (PARTITION BY l.campaign_id ORDER BY SUM(l.net_line_revenue) DESC) AS rn
    FROM v_order_lines l
    WHERE l.campaign_id IS NOT NULL
    GROUP BY l.campaign_id, l.product_name
)
SELECT r.campaign_id, c.campaign_name, r.rn AS product_rank, r.product_name, r.units, r.net_revenue
FROM ranked r JOIN ad_campaigns c ON c.campaign_id = r.campaign_id
WHERE r.rn <= 3
ORDER BY r.campaign_id, r.rn;
