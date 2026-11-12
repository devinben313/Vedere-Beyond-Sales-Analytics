"""
05_export_tableau.py
--------------------
Exports denormalized, Tableau-ready extracts to tableau/data/. Each file feeds
one or more worksheets of the Vèdere Beyond dashboard (see tableau/DASHBOARD_GUIDE.md).
Customer names / emails are excluded - extracts carry customer_id only.

Usage:  python scripts/05_export_tableau.py
"""

from __future__ import annotations

import pandas as pd

from vb_analytics import ROOT, campaign_actions, connect, reallocation_plan, run_query, sql

OUT = ROOT / "tableau" / "data"

EXTRACTS = {
    # Grain: one row per order line (non-refunded). Product profitability, category mix.
    "vb_order_lines": """
        SELECT l.*, c.acquisition_channel, c.cohort_month,
               ac.campaign_name, ac.strategy AS campaign_strategy
        FROM v_order_lines l
        JOIN customers c        ON c.customer_id = l.customer_id
        LEFT JOIN ad_campaigns ac ON ac.campaign_id = l.campaign_id""",
    # Grain: one row per order. Revenue trend, AOV, new vs returning, discounts.
    "vb_orders": """
        SELECT o.order_id, o.customer_id, o.order_date, o.order_month, o.order_status, o.is_refunded,
               o.customer_order_number, o.is_first_order,
               CASE WHEN o.is_first_order = 1 THEN 'New' ELSE 'Returning' END AS customer_type,
               o.attribution_channel, o.campaign_id, ac.campaign_name, ac.strategy AS campaign_strategy,
               NULLIF(o.discount_code, '') AS discount_code, o.units, o.gross_sales, o.discount,
               o.refund_amount, o.net_sales, o.shipping_charged, o.cogs, o.fulfillment_cost,
               o.payment_fees, o.contribution_margin, c.acquisition_channel, c.cohort_month, c.state
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        LEFT JOIN ad_campaigns ac ON ac.campaign_id = o.campaign_id""",
    # Grain: campaign x day. Spend / ROAS trends, funnel.
    "vb_ad_performance_daily": """
        SELECT a.*, c.campaign_name, c.strategy, c.objective, c.creative_type, c.funnel_stage
        FROM ad_performance_daily a JOIN ad_campaigns c ON c.campaign_id = a.campaign_id""",
    # Grain: one row per customer (no PII). Customer behaviour, LTV.
    "vb_customers": """
        SELECT customer_id, city, state, accepts_marketing, acquisition_channel, acquisition_campaign_id,
               first_order_date, cohort_month, total_orders, is_repeat_customer,
               lifetime_revenue, lifetime_contribution, date(last_order_ts) AS last_order_date
        FROM customers""",
    "vb_monthly_kpis": "SELECT * FROM v_monthly_kpis ORDER BY month",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = connect()
    for name, q in EXTRACTS.items():
        df = sql(q, con)
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"  {name + '.csv':<32} {len(df):>6,} rows")

    run_query("cohort_retention", con).to_csv(OUT / "vb_cohort_retention.csv", index=False)
    plan, s = reallocation_plan(con)
    actions = campaign_actions(run_query("campaign_roas", con), s["breakeven_roas"])
    actions.to_csv(OUT / "vb_campaign_scorecard.csv", index=False)
    run_query("product_margins", con).to_csv(OUT / "vb_product_margins.csv", index=False)
    plan.to_csv(OUT / "vb_budget_reallocation.csv", index=False)
    con.close()
    for n in ["vb_cohort_retention", "vb_campaign_scorecard", "vb_product_margins", "vb_budget_reallocation"]:
        print(f"  {n + '.csv':<32} {len(pd.read_csv(OUT / f'{n}.csv')):>6,} rows")
    print(f"\nTableau extracts -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
