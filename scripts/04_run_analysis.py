"""
04_run_analysis.py
------------------
Runs every SQL query in sql/analysis/ against the SQLite database, saves each
result to reports/query_results/<query>.csv, then builds the campaign action
list and the ad budget reallocation plan.

Usage:  python scripts/04_run_analysis.py
"""

from __future__ import annotations

import pandas as pd

from vb_analytics import RESULTS_DIR, campaign_actions, connect, query_files, reallocation_plan

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    con = connect()
    results = {}
    for path in query_files():
        df = pd.read_sql_query(path.read_text(), con)
        df.to_csv(RESULTS_DIR / f"{path.stem}.csv", index=False)
        results[path.stem] = df
        print(f"  {path.name:<42} -> {len(df):>4} rows")

    plan, s = reallocation_plan(con)
    plan.round(4).to_csv(RESULTS_DIR / "15_budget_reallocation_plan.csv", index=False)
    actions = campaign_actions(results["06_campaign_roas"], s["breakeven_roas"])
    actions[["campaign_id", "campaign_name", "strategy", "spend", "attributed_revenue", "roas",
             "cost_per_new_customer", "profit_after_ad_spend", "action"]].to_csv(
        RESULTS_DIR / "16_campaign_actions.csv", index=False)
    con.close()

    k = results["01_kpi_summary"].iloc[0]
    print("\n=== Headline KPIs ===")
    print(f"Net revenue ${k.net_revenue:,.0f} | customers {k.unique_customers} | orders {k.orders} | "
          f"AOV ${k.avg_order_value:.2f}")
    print(f"Meta spend ${k.meta_ad_spend:,.0f} | ROAS {k.meta_roas:.2f}x | MER {k.blended_mer:.2f}x | "
          f"paid CAC ${k.paid_cac:.2f} | repeat rate {k.repeat_purchase_rate_pct}%")

    print("\n=== Campaign actions (break-even ROAS {:.2f}x) ===".format(s["breakeven_roas"]))
    print(actions[["campaign_id", "campaign_name", "roas", "action"]].to_string(index=False))

    print(f"\n=== Budget reallocation ({s['months']}-month budget ${s['budget']:,.0f}) ===")
    print(plan[["strategy", "roas", "current_share", "proposed_share", "budget_change",
                "projected_revenue"]].round(2).to_string(index=False))
    print(f"Attributed revenue ${s['current_revenue']:,.0f} -> ${s['projected_revenue']:,.0f} "
          f"(+{s['projected_revenue'] / s['current_revenue'] - 1:.0%}); ROAS {s['current_roas']:.2f}x -> "
          f"{s['projected_roas']:.2f}x; profit after ads ${s['current_profit']:,.0f} -> ${s['projected_profit']:,.0f}")
    print(f"\nResults saved -> reports/query_results/")


if __name__ == "__main__":
    main()
