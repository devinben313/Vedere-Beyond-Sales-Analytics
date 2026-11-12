"""
vb_analytics.py
---------------
Shared helpers used by the pipeline scripts and the Jupyter notebook:
database access, the SQL query runner and the ad budget reallocation model.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "vedere_beyond.db"
SQL_DIR = ROOT / "sql" / "analysis"
RESULTS_DIR = ROOT / "reports" / "query_results"

# ---------------------------------------------------------------------------
# Database / SQL
# ---------------------------------------------------------------------------


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"{DB_PATH} not found - run scripts/03_build_database.py first")
    return sqlite3.connect(DB_PATH)


def query_files() -> list[Path]:
    return sorted(SQL_DIR.glob("*.sql"))


def run_query(name: str, con: sqlite3.Connection | None = None) -> pd.DataFrame:
    """Run sql/analysis/<name>.sql (name may omit the numeric prefix)."""
    matches = [p for p in query_files() if p.stem == name or p.stem.split("_", 1)[1] == name]
    if not matches:
        raise KeyError(f"no query named {name!r} in {SQL_DIR}")
    own = con is None
    con = con or connect()
    try:
        return pd.read_sql_query(matches[0].read_text(), con)
    finally:
        if own:
            con.close()


def sql(text: str, con: sqlite3.Connection | None = None) -> pd.DataFrame:
    """Run an ad-hoc SQL string."""
    own = con is None
    con = con or connect()
    try:
        return pd.read_sql_query(text, con)
    finally:
        if own:
            con.close()


# ---------------------------------------------------------------------------
# Budget reallocation model
# ---------------------------------------------------------------------------
# Proposed share of Meta budget by strategy, derived from the campaign
# scorecard (see README "Recommendations"). Shares sum to 1.
PROPOSED_SHARE = {
    "Retargeting": 0.24,
    "Lookalike Prospecting": 0.22,
    "UGC / Reels": 0.18,
    "Seasonal Promotion": 0.18,
    "Product Drop": 0.10,
    "Interest Prospecting": 0.08,
    "Broad Prospecting": 0.00,
    "Brand Awareness": 0.00,
}
SCALE_ELASTICITY = 0.70      # revenue ~ spend^0.7 when scaling up (diminishing returns)
RETARGETING_MAX_SCALE = 1.6  # retargeting is capped by warm-audience size


def campaign_actions(scorecard: pd.DataFrame, breakeven_roas: float) -> pd.DataFrame:
    """Label each campaign Scale / Optimize / Cut relative to break-even ROAS."""
    df = scorecard.copy()
    df["action"] = np.select(
        [df.roas >= 3.0, df.roas >= 1.25 * breakeven_roas],
        ["Scale", "Optimize & maintain"], default="Cut / restructure")
    return df


def reallocation_plan(con: sqlite3.Connection | None = None, months: int = 12) -> tuple[pd.DataFrame, dict]:
    """
    Re-allocate a flat forward budget (historic average monthly spend x months)
    across campaign strategies and project attributed revenue and profit.

    Projection logic
      * baseline spend per strategy = historic share x forward budget
      * cutting spend loses revenue at the strategy's historic average ROAS (conservative)
      * adding spend earns revenue on a concave curve: R = ROAS x B x (S/B)^0.7
      * profit after ads = revenue x contribution-margin rate - spend
    """
    own = con is None
    con = con or connect()
    try:
        strat = sql("""
            SELECT strategy, SUM(spend) AS spend, SUM(purchase_value) AS revenue,
                   SUM(contribution_margin) AS contribution
            FROM v_campaign_performance GROUP BY strategy""", con)
        n_months = sql("SELECT COUNT(DISTINCT strftime('%Y-%m', date)) AS n FROM ad_performance_daily", con).n[0]
    finally:
        if own:
            con.close()

    cm_rate = strat.contribution.sum() / strat.revenue.sum()
    budget = strat.spend.sum() / n_months * months
    strat["roas"] = strat.revenue / strat.spend
    strat["current_share"] = strat.spend / strat.spend.sum()
    strat["current_budget"] = strat.current_share * budget
    strat["current_revenue"] = strat.current_budget * strat.roas
    strat["proposed_share"] = strat.strategy.map(PROPOSED_SHARE).fillna(0.0)
    strat["proposed_budget"] = strat.proposed_share * budget

    ratio = strat.proposed_budget / strat.current_budget
    if (strat.strategy.eq("Retargeting") & ratio.gt(RETARGETING_MAX_SCALE)).any():
        raise ValueError("retargeting scaled beyond audience cap")
    scaled = strat.roas * strat.current_budget * np.power(ratio.clip(lower=1.0), SCALE_ELASTICITY)
    strat["projected_revenue"] = np.where(ratio >= 1.0, scaled, strat.proposed_budget * strat.roas)
    strat["projected_roas"] = strat.projected_revenue / strat.proposed_budget.replace(0, np.nan)
    strat["current_profit"] = strat.current_revenue * cm_rate - strat.current_budget
    strat["projected_profit"] = strat.projected_revenue * cm_rate - strat.proposed_budget
    strat["budget_change"] = strat.proposed_budget - strat.current_budget

    plan = strat[["strategy", "roas", "current_share", "current_budget", "proposed_share", "proposed_budget",
                  "budget_change", "current_revenue", "projected_revenue", "projected_roas",
                  "current_profit", "projected_profit"]].sort_values("proposed_share", ascending=False)
    summary = {
        "months": months,
        "budget": budget,
        "contribution_margin_rate": cm_rate,
        "breakeven_roas": 1 / cm_rate,
        "current_revenue": plan.current_revenue.sum(),
        "projected_revenue": plan.projected_revenue.sum(),
        "current_roas": plan.current_revenue.sum() / budget,
        "projected_roas": plan.projected_revenue.sum() / budget,
        "current_profit": plan.current_profit.sum(),
        "projected_profit": plan.projected_profit.sum(),
    }
    return plan.reset_index(drop=True), summary
