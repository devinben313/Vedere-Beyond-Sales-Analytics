"""
02_clean_transform.py
---------------------
Cleans, standardizes, enriches and combines the raw exports in data/raw/
into analysis-ready tables in data/processed/.

Cleaning steps
  products    : strip whitespace, parse currency strings, compute unit margin
  customers   : de-duplicate, normalize email / state, map free-text survey
                answers to a standard acquisition channel (inferred from the
                first order's UTM tags when the survey was skipped)
  orders      : drop test / voided orders and duplicate rows, parse mixed date
                formats and currency strings, normalize UTM values, resolve
                customer_id via email, map utm_campaign -> campaign_id,
                classify attribution channel, sequence each customer's orders
  order_items : drop zero-quantity lines, attach unit cost, compute line COGS
  meta ads    : rename columns to snake_case, fill blank metric cells with 0,
                map Meta campaign IDs to internal campaign IDs

Derived economics (per order)
  gross_sales      = sum(quantity * unit_price)
  net_sales        = gross_sales - discount        (0 when refunded)
  cogs             = sum(quantity * unit_cost)     (0 when refunded - stock restocked)
  fulfillment_cost = $5.50 pick/pack/ship + $0.50 per additional unit (web orders)
  payment_fees     = 2.9% + $0.30 of amount charged (web) / 2.6% + $0.10 (POS)
  contribution     = net_sales + shipping_charged - cogs - fulfillment - fees

Usage:  python scripts/02_clean_transform.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

STATE_FIX = {"georgia": "GA", "texas": "TX", "california": "CA", "new york": "NY", "florida": "FL"}
CHANNEL_FROM_SURVEY = {
    "instagram ad": "Meta Ads", "facebook ad": "Meta Ads", "saw an ad on instagram": "Meta Ads",
    "instagram (organic)": "Instagram Organic", "instagram": "Instagram Organic", "ig page": "Instagram Organic",
    "friend/family": "Referral", "friend": "Referral", "word of mouth": "Referral",
    "tiktok": "TikTok Organic",
    "pop-up event": "Pop-up Event", "pop up shop": "Pop-up Event",
}
CHANNEL_FROM_UTM = {
    "facebook": "Meta Ads", "fb": "Meta Ads", "instagram": "Meta Ads", "ig": "Meta Ads",
    "instagram_organic": "Instagram Organic", "referral": "Referral", "tiktok": "TikTok Organic",
    "pos": "Pop-up Event", "email": "Email", "sms": "SMS", "direct": "Direct",
}


def money(s: pd.Series) -> pd.Series:
    """'$1,234.50' -> 1234.5"""
    return pd.to_numeric(s.astype(str).str.replace(r"[$,\s]", "", regex=True), errors="coerce")


log: list[str] = []


def note(msg: str) -> None:
    log.append(msg)
    print("  -", msg)


# ---------------------------------------------------------------------------
print("Cleaning products ...")
products = pd.read_csv(RAW / "products.csv")
products["product_name"] = products.product_name.str.strip()
products["retail_price"] = money(products.retail_price)
products["launch_date"] = pd.to_datetime(products.launch_date)
products["unit_margin"] = products.retail_price - products.unit_cost
products["margin_pct"] = (products.unit_margin / products.retail_price).round(4)
products.insert(0, "product_id", [f"P{i + 1:02d}" for i in range(len(products))])
note(f"products: {len(products)} SKUs, prices parsed from currency strings")

# ---------------------------------------------------------------------------
print("Cleaning Meta campaigns & daily ad performance ...")
campaigns = pd.read_csv(RAW / "meta_campaigns.csv", dtype={"meta_campaign_id": str})
campaigns["start_date"] = pd.to_datetime(campaigns.start_date)
campaigns["end_date"] = pd.to_datetime(campaigns.end_date)
campaigns["funnel_stage"] = np.select(
    [campaigns.strategy.eq("Retargeting"), campaigns.objective.eq("Awareness")],
    ["Bottom (Retargeting)", "Top (Awareness)"], default="Middle (Prospecting / Conversion)")

ads = pd.read_csv(RAW / "meta_ads_daily.csv", dtype={"Campaign ID": str})
ads = ads.rename(columns={
    "Reporting starts": "date", "Campaign ID": "meta_campaign_id", "Campaign name": "campaign_name",
    "Amount spent (USD)": "spend", "Impressions": "impressions", "Reach": "reach",
    "Clicks (all)": "clicks", "Link clicks": "link_clicks", "Landing page views": "landing_page_views",
    "Adds to cart": "add_to_cart", "Checkouts initiated": "checkouts_initiated",
    "Purchases": "purchases", "Purchases conversion value": "purchase_value",
}).drop(columns=["Reporting ends"])
blank_cells = int(ads[["add_to_cart", "checkouts_initiated", "purchases", "purchase_value"]].isna().sum().sum())
metric_cols = ["spend", "impressions", "reach", "clicks", "link_clicks", "landing_page_views",
               "add_to_cart", "checkouts_initiated", "purchases", "purchase_value"]
ads[metric_cols] = ads[metric_cols].fillna(0)
for c in ["impressions", "reach", "clicks", "link_clicks", "landing_page_views",
          "add_to_cart", "checkouts_initiated", "purchases"]:
    ads[c] = ads[c].astype(int)
ads["date"] = pd.to_datetime(ads.date)
ads = ads.merge(campaigns[["meta_campaign_id", "campaign_id"]], on="meta_campaign_id", how="left")
assert ads.campaign_id.notna().all(), "unmapped Meta campaign IDs"
ads = ads[["date", "campaign_id"] + metric_cols]
note(f"meta ads: {len(ads):,} campaign-day rows, {blank_cells:,} blank metric cells filled with 0")

# ---------------------------------------------------------------------------
print("Cleaning customers ...")
cust = pd.read_csv(RAW / "customers.csv", keep_default_na=False)
n0 = len(cust)
cust = cust.drop_duplicates()
note(f"customers: removed {n0 - len(cust)} exact duplicate rows")
cust["email"] = cust.email.str.strip().str.lower()
assert cust.email.is_unique and cust.customer_id.is_unique
cust["state"] = cust.state.str.strip().map(lambda s: STATE_FIX.get(s.lower(), s.upper()))
cust["city"] = cust.city.str.strip().replace("", "Unknown")
cust["created_at"] = pd.to_datetime(cust.created_at)
cust["accepts_marketing"] = cust.accepts_marketing.eq("yes")
cust["survey_channel"] = cust.how_did_you_hear.str.strip().str.lower().map(CHANNEL_FROM_SURVEY)

# ---------------------------------------------------------------------------
print("Cleaning orders ...")
orders = pd.read_csv(RAW / "orders.csv", keep_default_na=False)
n0 = len(orders)
orders = orders.drop_duplicates()
note(f"orders: removed {n0 - len(orders)} duplicate rows")
is_test = orders.email.str.contains("test@vederebeyond", case=False) | orders.name.str.startswith("#T")
note(f"orders: removed {int(is_test.sum())} test / voided orders")
orders = orders[~is_test].copy()

orders["order_id"] = orders.name.str.lstrip("#").astype(int)
orders["email"] = orders.email.str.strip().str.lower()
orders["order_ts"] = pd.to_datetime(orders.created_at, format="mixed")
note(f"orders: parsed {int(orders.created_at.str.contains('/').sum())} US-format (MM/DD/YYYY) timestamps")
orders["subtotal"] = money(orders.subtotal)
orders["total"] = money(orders.total)
orders["discount_amount"] = pd.to_numeric(orders.discount_amount)
orders["shipping"] = pd.to_numeric(orders.shipping)
orders["utm_source"] = orders.utm_source.str.strip().str.lower()
orders["utm_campaign"] = orders.utm_campaign.str.strip().str.lower()

orders = orders.merge(cust[["customer_id", "email"]], on="email", how="left")
assert orders.customer_id.notna().all(), "orders without a matching customer"
orders = orders.merge(campaigns[["utm_campaign", "campaign_id"]].rename(columns={"utm_campaign": "uc"}),
                      left_on="utm_campaign", right_on="uc", how="left").drop(columns="uc")

src = np.where(orders.source_name.eq("pos"), "pos", orders.utm_source.replace("", "direct"))
orders["attribution_channel"] = pd.Series(src, index=orders.index).map(CHANNEL_FROM_UTM)
orders.loc[orders.campaign_id.notna(), "attribution_channel"] = "Meta Ads"
assert orders.attribution_channel.notna().all()

orders = orders.sort_values(["customer_id", "order_ts"])
orders["customer_order_number"] = orders.groupby("customer_id").cumcount() + 1
orders["is_first_order"] = orders.customer_order_number.eq(1)
orders["order_status"] = orders.financial_status
orders["is_refunded"] = orders.order_status.eq("refunded")

# ---------------------------------------------------------------------------
print("Cleaning order items ...")
items = pd.read_csv(RAW / "order_items.csv")
n0 = len(items)
items = items[items.quantity > 0].copy()
note(f"order_items: removed {n0 - len(items)} zero-quantity lines")
items["order_id"] = items.order_id.str.lstrip("#").astype(int)
items = items[items.order_id.isin(orders.order_id)]
items["product_name"] = items.product_name.str.strip()
items = items.merge(products[["sku", "product_id", "unit_cost"]], on="sku", how="left")
assert items.product_id.notna().all()
items["line_revenue"] = items.quantity * items.unit_price
items["line_cogs"] = items.quantity * items.unit_cost
items.insert(0, "order_item_id", range(1, len(items) + 1))

# ---------------------------------------------------------------------------
print("Building order-level economics ...")
agg = items.groupby("order_id").agg(units=("quantity", "sum"), line_count=("sku", "count"),
                                    gross_sales=("line_revenue", "sum"), item_cogs=("line_cogs", "sum"))
orders = orders.merge(agg, on="order_id", how="left")
mismatch = (orders.gross_sales - orders.subtotal).abs().gt(0.01).sum()
assert mismatch == 0, f"{mismatch} orders whose line items do not sum to subtotal"

refund = orders.is_refunded
pos = orders.source_name.eq("pos")
orders["discount"] = orders.discount_amount
orders["net_sales"] = np.where(refund, 0.0, orders.gross_sales - orders.discount)
orders["refund_amount"] = np.where(refund, orders.gross_sales - orders.discount, 0.0)
orders["shipping_charged"] = np.where(refund, 0.0, orders.shipping)
orders["cogs"] = np.where(refund, 0.0, orders.item_cogs)
orders["fulfillment_cost"] = np.where(pos, 0.0, 5.50 + 0.50 * (orders.units - 1))
charged = orders.gross_sales - orders.discount + orders.shipping
orders["payment_fees"] = np.where(pos, charged * 0.026 + 0.10, charged * 0.029 + 0.30).round(2)
orders["contribution_margin"] = (orders.net_sales + orders.shipping_charged - orders.cogs
                                 - orders.fulfillment_cost - orders.payment_fees).round(2)
orders["order_date"] = orders.order_ts.dt.normalize()
orders["order_month"] = orders.order_ts.dt.to_period("M").astype(str)

orders = orders[[
    "order_id", "customer_id", "order_ts", "order_date", "order_month", "order_status", "is_refunded",
    "customer_order_number", "is_first_order", "source_name", "utm_source", "utm_medium", "utm_campaign",
    "attribution_channel", "campaign_id", "discount_code", "units", "line_count", "gross_sales",
    "discount", "refund_amount", "net_sales", "shipping_charged", "cogs", "fulfillment_cost",
    "payment_fees", "contribution_margin",
]].sort_values("order_id").reset_index(drop=True)

# ---------------------------------------------------------------------------
print("Enriching customers ...")
# drop_duplicates (not groupby.first, which skips NULLs column-by-column)
first = orders.sort_values("order_ts").drop_duplicates("customer_id").set_index("customer_id")
cust = cust.merge(first[["order_ts", "attribution_channel", "campaign_id"]].rename(columns={
    "order_ts": "first_order_ts", "attribution_channel": "first_touch_channel",
    "campaign_id": "acquisition_campaign_id"}), left_on="customer_id", right_index=True, how="left")
assert cust.first_order_ts.notna().all(), "customer with no orders"
missing = cust.survey_channel.isna()
note(f"customers: {int(missing.sum())} skipped the survey -> channel inferred from first-order UTM")
cust["acquisition_channel"] = cust.survey_channel.fillna(cust.first_touch_channel)
# A purchase pixel-attributed to a Meta campaign is the source of truth for paid acquisition.
cust.loc[cust.acquisition_campaign_id.notna(), "acquisition_channel"] = "Meta Ads"
cust.loc[cust.acquisition_channel.ne("Meta Ads"), "acquisition_campaign_id"] = np.nan
cust["first_order_date"] = cust.first_order_ts.dt.normalize()
cust["cohort_month"] = cust.first_order_ts.dt.to_period("M").astype(str)

life = orders[~orders.is_refunded].groupby("customer_id").agg(
    total_orders=("order_id", "count"), lifetime_revenue=("net_sales", "sum"),
    lifetime_contribution=("contribution_margin", "sum"), last_order_ts=("order_ts", "max"))
cust = cust.merge(life, left_on="customer_id", right_index=True, how="left")
cust[["total_orders", "lifetime_revenue", "lifetime_contribution"]] = (
    cust[["total_orders", "lifetime_revenue", "lifetime_contribution"]].fillna(0))
cust["total_orders"] = cust.total_orders.astype(int)
cust["is_repeat_customer"] = cust.total_orders >= 2
cust = cust[["customer_id", "first_name", "last_name", "email", "city", "state", "accepts_marketing",
             "acquisition_channel", "acquisition_campaign_id", "first_order_date", "cohort_month",
             "total_orders", "is_repeat_customer", "lifetime_revenue", "lifetime_contribution",
             "last_order_ts"]].sort_values("customer_id").reset_index(drop=True)

# ---------------------------------------------------------------------------
# Data-quality checks between sources
paid = orders[~orders.is_refunded]
shop_attr = paid.groupby("campaign_id").net_sales.sum().round(2)
meta_attr = ads.groupby("campaign_id").purchase_value.sum().round(2)
assert (shop_attr.reindex(meta_attr.index).fillna(0) - meta_attr).abs().max() < 0.05, \
    "Meta-reported purchase value does not reconcile with Shopify orders"
note("reconciliation: Meta purchase value matches Shopify net sales for every campaign")

# ---------------------------------------------------------------------------
items.to_csv(OUT / "order_items.csv", index=False)
orders.to_csv(OUT / "orders.csv", index=False)
cust.to_csv(OUT / "customers.csv", index=False)
products.to_csv(OUT / "products.csv", index=False)
campaigns.to_csv(OUT / "ad_campaigns.csv", index=False)
ads.to_csv(OUT / "ad_performance_daily.csv", index=False)
(OUT / "cleaning_log.txt").write_text("\n".join(log) + "\n")

print(f"\nWrote processed tables -> {OUT.relative_to(ROOT)}")
print(f"  customers {len(cust)}, orders {len(orders)} ({int(orders.is_refunded.sum())} refunded), "
      f"items {len(items)}, ad rows {len(ads)}")
print(f"  net revenue ${paid.net_sales.sum():,.2f} | Meta spend ${ads.spend.sum():,.2f} | "
      f"ROAS {ads.purchase_value.sum() / ads.spend.sum():.2f}x")
