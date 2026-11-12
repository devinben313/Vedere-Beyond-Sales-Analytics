"""
01_generate_data.py
-------------------
Generates a realistic *synthetic* dataset for Vèdere Beyond, an independent
streetwear / clothing brand, covering 14 months of operations
(2024-09-01 through 2025-10-31).

Outputs (data/raw/) intentionally mimic the messy exports a small brand
actually works with:

    products.csv        - product catalog export
    customers.csv       - customer export incl. post-purchase survey answer
    orders.csv          - Shopify-style order export (joined to customers by email)
    order_items.csv     - order line items
    meta_campaigns.csv  - Meta Ads campaign settings export
    meta_ads_daily.csv  - Meta Ads Manager daily campaign report

Realistic data-quality issues are injected on purpose (duplicate rows,
inconsistent casing / whitespace, mixed date formats, currency strings,
test orders, blank metric cells, missing survey answers) so that
02_clean_transform.py has real cleaning work to do.

The generator is calibrated so the cleaned data lands on the brand's actual
headline numbers: > $20,000 net revenue, > 240 unique customers and an
overall Meta-attributed ROAS between 2.5x and 3.0x.

Usage:  python scripts/01_generate_data.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 313
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2024-09-01")
END = pd.Timestamp("2025-10-31")
TARGET_ROAS = 2.72  # overall Meta-attributed ROAS the brand saw (2.5x - 3.0x)

# ---------------------------------------------------------------------------
# 1. Product catalog
# ---------------------------------------------------------------------------
PRODUCTS = [
    # sku, name, category, collection, price, unit_cost, launch, popularity
    ("VB-TEE-ESS-BLK", "Essential Logo Tee - Black", "Tees", "Core", 32, 9.50, "2024-09-01", 10),
    ("VB-TEE-ESS-WHT", "Essential Logo Tee - White", "Tees", "Core", 32, 9.50, "2024-09-01", 8),
    ("VB-TEE-VIS", "Visionary Graphic Tee", "Tees", "Core", 38, 11.00, "2024-09-01", 7),
    ("VB-HOD-SIG-BLK", "Signature Heavyweight Hoodie - Black", "Hoodies", "Core", 78, 24.00, "2024-09-01", 9),
    ("VB-HOD-SIG-CRM", "Signature Heavyweight Hoodie - Cream", "Hoodies", "Core", 78, 24.00, "2024-10-01", 6),
    ("VB-CRW-BYD", "Beyond Crewneck", "Crewnecks", "Fall/Winter 2024", 64, 19.50, "2024-10-15", 5),
    ("VB-SWP-SIG", "Signature Sweatpants", "Bottoms", "Core", 62, 19.00, "2024-09-01", 6),
    ("VB-HAT-DAD", "Embroidered Dad Hat", "Accessories", "Core", 28, 7.00, "2024-09-01", 5),
    ("VB-BEN-KNT", "Knit Beanie", "Accessories", "Fall/Winter 2024", 24, 6.50, "2024-11-01", 4),
    ("VB-TEE-SPR", "Spring Bloom Graphic Tee", "Tees", "Spring 2025", 36, 11.50, "2025-03-10", 6),
    ("VB-WBR-SPR", "Lightweight Windbreaker", "Outerwear", "Spring 2025", 88, 43.00, "2025-03-10", 2),
    ("VB-SHT-MSH", "Mesh Shorts", "Bottoms", "Summer 2025", 40, 12.50, "2025-06-01", 5),
    ("VB-TEE-BOX", "Summer Boxy Tee", "Tees", "Summer 2025", 34, 10.00, "2025-06-01", 5),
    ("VB-TOT-CNV", "Canvas Tote Bag", "Accessories", "Core", 22, 9.00, "2025-04-01", 2),
    ("VB-HOD-ZIP", "Fall '25 Zip Hoodie", "Hoodies", "Fall 2025", 84, 27.00, "2025-09-05", 7),
]
products = pd.DataFrame(
    PRODUCTS,
    columns=["sku", "product_name", "category", "collection", "retail_price",
             "unit_cost", "launch_date", "popularity"],
)
products["launch_date"] = pd.to_datetime(products["launch_date"])
APPAREL_SIZES = ["S", "M", "L", "XL", "XXL"]
SIZE_P = [0.14, 0.31, 0.30, 0.18, 0.07]

# ---------------------------------------------------------------------------
# 2. Meta campaign plan
# ---------------------------------------------------------------------------
# planned_new = first-time customers the campaign acquired (pixel-attributed)
# target_roas = relative efficiency used to back out spend
CAMPAIGNS = [
    # id, name, utm, objective, strategy, audience, creative, start, end, new, roas, cpm, ctr
    ("C01", "VB | Launch | Broad Prospecting", "launch_broad", "Sales", "Broad Prospecting",
     "Broad 18-34, US", "Static Image", "2024-09-01", "2024-10-20", 16, 1.70, 9.5, 0.0085),
    ("C02", "VB | Interest | Streetwear Enthusiasts", "interest_streetwear", "Sales", "Interest Prospecting",
     "Interests: streetwear, sneakers, hypebeast", "Carousel", "2024-10-01", "2025-03-31", 24, 2.30, 11.0, 0.0110),
    ("C03", "VB | BFCM 2024 | 25% Off", "bfcm_2024", "Sales", "Seasonal Promotion",
     "Broad + warm audiences", "Static Image", "2024-11-20", "2024-12-02", 22, 4.10, 16.5, 0.0175),
    ("C04", "VB | Holiday Gifting 2024", "holiday_gifting", "Sales", "Seasonal Promotion",
     "Gift-givers 25-44", "Carousel", "2024-12-03", "2024-12-20", 12, 3.00, 14.0, 0.0130),
    ("C05", "VB | Retargeting | Site Visitors + ATC", "retargeting_always_on", "Sales", "Retargeting",
     "Site visitors 30d, add-to-cart 14d, IG engagers", "Dynamic Product Ads", "2024-09-15", "2025-10-31", 18, 5.20, 18.0, 0.0210),
    ("C06", "VB | Lookalike 1% | Purchasers", "lal_1pct_purchasers", "Sales", "Lookalike Prospecting",
     "1% lookalike of purchasers", "UGC Video", "2025-02-01", "2025-10-31", 28, 3.40, 12.0, 0.0145),
    ("C07", "VB | Spring Drop 2025 | Video", "spring_drop_video", "Sales", "Product Drop",
     "Broad 18-34 + interests", "Studio Video", "2025-03-08", "2025-04-30", 10, 1.90, 11.5, 0.0095),
    ("C08", "VB | Summer Collection | Reels UGC", "summer_reels_ugc", "Sales", "UGC / Reels",
     "Broad 18-34, Reels placements", "UGC Reels", "2025-06-01", "2025-08-31", 16, 3.10, 8.5, 0.0160),
    ("C09", "VB | Brand Awareness | Reach", "awareness_reach", "Awareness", "Brand Awareness",
     "Broad 18-44, US", "Studio Video", "2025-04-15", "2025-06-30", 3, None, 5.0, 0.0045),
    ("C10", "VB | Fall Drop 2025 | Carousel", "fall_drop_carousel", "Sales", "Product Drop",
     "Advantage+ audience", "Carousel", "2025-09-01", "2025-10-31", 13, 2.50, 12.5, 0.0120),
]
campaigns = pd.DataFrame(
    CAMPAIGNS,
    columns=["campaign_id", "campaign_name", "utm_campaign", "objective", "strategy", "audience",
             "creative_type", "start_date", "end_date", "planned_new", "target_roas", "cpm", "ctr"],
)
campaigns["start_date"] = pd.to_datetime(campaigns["start_date"])
campaigns["end_date"] = pd.to_datetime(campaigns["end_date"])
AWARENESS_FIXED_SPEND = 640.00  # awareness campaign spend is set, not ROAS-driven

# Product affinities by campaign (creative featured these products)
CAMPAIGN_PRODUCT_BOOST = {
    "C03": {"VB-HOD-SIG-BLK": 2.0, "VB-HOD-SIG-CRM": 2.0, "VB-CRW-BYD": 1.8, "VB-SWP-SIG": 1.5},
    "C04": {"VB-BEN-KNT": 2.5, "VB-HAT-DAD": 2.0, "VB-CRW-BYD": 1.8, "VB-HOD-SIG-CRM": 1.6},
    "C07": {"VB-TEE-SPR": 3.0, "VB-WBR-SPR": 3.0},
    "C08": {"VB-SHT-MSH": 3.0, "VB-TEE-BOX": 3.0},
    "C10": {"VB-HOD-ZIP": 4.0},
}

# ---------------------------------------------------------------------------
# 3. Customers & first purchase dates
# ---------------------------------------------------------------------------
FIRST_NAMES = """James Mary Michael Patricia Robert Jennifer John Linda David Elizabeth William
Barbara Richard Susan Joseph Jessica Thomas Sarah Christopher Karen Charles Lisa Daniel Nancy
Matthew Betty Anthony Sandra Mark Ashley Donald Kimberly Steven Emily Andrew Donna Paul Michelle
Joshua Carol Kenneth Amanda Kevin Melissa Brian Deborah Timothy Stephanie Ronald Rebecca Jason
Laura George Sharon Edward Cynthia Jeffrey Kathleen Ryan Amy Jacob Angela Nicholas Shirley Eric
Brenda Jonathan Emma Justin Anna Brandon Nicole Samuel Samantha Benjamin Katherine Gregory Christine
Alexander Rachel Patrick Janet Jack Maria Dennis Olivia Tyler Heather Aaron Diane Jose Julie
Adam Victoria Nathan Kelly Zachary Lauren Kyle Christina Noah Megan Ethan Andrea Jordan Destiny
Malik Aaliyah Darius Imani Andre Jasmine Marcus Kiara Xavier Nia Isaiah Tiana Elijah Zoe Carlos
Sofia Diego Camila Luis Valeria Mateo Isabella Kai Mia Jalen Ava Devin Layla Trey Brianna""".split()
LAST_NAMES = """Smith Johnson Williams Brown Jones Garcia Miller Davis Rodriguez Martinez Hernandez
Lopez Gonzalez Wilson Anderson Thomas Taylor Moore Jackson Martin Lee Perez Thompson White Harris
Sanchez Clark Ramirez Lewis Robinson Walker Young Allen King Wright Scott Torres Nguyen Hill Flores
Green Adams Nelson Baker Hall Rivera Campbell Mitchell Carter Roberts Gomez Phillips Evans Turner
Diaz Parker Cruz Edwards Collins Reyes Stewart Morris Morales Murphy Cook Rogers Gutierrez Ortiz
Morgan Cooper Peterson Bailey Reed Kelly Howard Ramos Kim Cox Ward Richardson Watson Brooks Chavez
Wood James Bennett Gray Mendoza Ruiz Hughes Price Alvarez Castillo Sanders Patel Myers Long Ross
Foster Jimenez Powell Jenkins Perry Russell Sullivan Bell Coleman Butler Henderson Barnes Washington""".split()
LOCATIONS = [  # city, state, weight
    ("Atlanta", "GA", 14), ("Houston", "TX", 9), ("Dallas", "TX", 7), ("Los Angeles", "CA", 9),
    ("New York", "NY", 9), ("Brooklyn", "NY", 6), ("Chicago", "IL", 7), ("Charlotte", "NC", 6),
    ("Miami", "FL", 6), ("Orlando", "FL", 4), ("Philadelphia", "PA", 5), ("Washington", "DC", 5),
    ("Nashville", "TN", 4), ("Phoenix", "AZ", 3), ("Seattle", "WA", 3), ("Denver", "CO", 3),
    ("Baltimore", "MD", 4), ("Detroit", "MI", 3), ("Columbus", "OH", 3), ("Raleigh", "NC", 3),
    ("San Diego", "CA", 3), ("Austin", "TX", 4), ("Boston", "MA", 3), ("New Orleans", "LA", 2),
]
loc_w = np.array([w for *_, w in LOCATIONS], dtype=float)
loc_w /= loc_w.sum()

# Organic channels and their month-of-year seasonality
ORGANIC_PLAN = {"Instagram Organic": 40, "Referral": 30, "TikTok Organic": 12}
POPUP_EVENTS = {"2024-12-14": 6, "2025-07-19": 5}  # pop-up shop dates -> customers acquired
MONTH_WEIGHT = {9: 1.1, 10: 1.0, 11: 1.6, 12: 1.7, 1: 0.6, 2: 0.6, 3: 0.9, 4: 0.8,
                5: 0.8, 6: 0.9, 7: 0.9, 8: 0.8}
all_days = pd.date_range(START, END, freq="D")


def day_weights(days: pd.DatetimeIndex) -> np.ndarray:
    """Weekday + seasonality weighting for picking purchase dates."""
    dow = np.array([1.0, 0.95, 0.95, 1.0, 1.1, 1.15, 1.25])[days.dayofweek]
    season = np.array([MONTH_WEIGHT[m] for m in days.month])
    w = dow * season
    return w / w.sum()


def pick_day(lo: pd.Timestamp, hi: pd.Timestamp) -> pd.Timestamp:
    days = pd.date_range(lo, hi, freq="D")
    return days[rng.choice(len(days), p=day_weights(days))]


cust_rows = []
used_names = set()


def new_customer(channel: str, first_date: pd.Timestamp, campaign_id: str | None):
    while True:
        fn, ln = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        if (fn, ln) not in used_names:
            used_names.add((fn, ln))
            break
    style = rng.integers(0, 4)
    num = rng.integers(1, 99)
    domain = rng.choice(["gmail.com", "gmail.com", "gmail.com", "yahoo.com", "icloud.com",
                         "outlook.com", "hotmail.com"])
    local = [f"{fn}.{ln}", f"{fn}{ln}{num}", f"{fn[0]}{ln}", f"{fn}_{ln[0]}{num}"][style].lower()
    city, state, _ = LOCATIONS[rng.choice(len(LOCATIONS), p=loc_w)]
    cust_rows.append(dict(first_name=fn, last_name=ln, email=f"{local}@{domain}", city=city,
                          state=state, true_channel=channel, acq_campaign=campaign_id,
                          first_order_date=first_date))


# Meta-acquired customers: date drawn from the campaign's active window
for c in campaigns.itertuples():
    for _ in range(c.planned_new):
        new_customer("Meta Ads", pick_day(c.start_date, c.end_date), c.campaign_id)

for ch, n in ORGANIC_PLAN.items():
    for _ in range(n):
        new_customer(ch, pick_day(START, END), None)

for d, n in POPUP_EVENTS.items():
    for _ in range(n):
        new_customer("Pop-up Event", pd.Timestamp(d), None)

customers = pd.DataFrame(cust_rows).sort_values("first_order_date").reset_index(drop=True)
customers["customer_id"] = [f"VB-C{1000 + i}" for i in range(len(customers))]

# ---------------------------------------------------------------------------
# 4. Orders (first + repeat) with attribution
# ---------------------------------------------------------------------------
# Probability of buying again, by acquisition channel
REPEAT_P = {"Meta Ads": 0.27, "Instagram Organic": 0.34, "Referral": 0.40,
            "TikTok Organic": 0.22, "Pop-up Event": 0.36}
FURTHER_REPEAT_P = 0.38


def active_campaigns(day: pd.Timestamp) -> pd.DataFrame:
    return campaigns[(campaigns.start_date <= day) & (campaigns.end_date >= day)]


def repeat_attribution(day: pd.Timestamp):
    """Where does a returning customer's order come from?"""
    act = active_campaigns(day)
    ids = set(act.campaign_id)
    if "C03" in ids and rng.random() < 0.55:
        return "facebook", "C03"
    if "C05" in ids and rng.random() < 0.40:
        return "instagram", "C05"
    src = rng.choice(["email", "direct", "instagram_organic", "sms"], p=[0.38, 0.30, 0.22, 0.10])
    return src, None


order_plan = []
for cu in customers.itertuples():
    # first order
    if cu.true_channel == "Meta Ads":
        src = rng.choice(["facebook", "instagram", "ig", "fb"], p=[0.35, 0.45, 0.12, 0.08])
        order_plan.append((cu.customer_id, cu.first_order_date, src, cu.acq_campaign, 1))
    else:
        src = {"Instagram Organic": "instagram_organic", "Referral": "referral",
               "TikTok Organic": "tiktok", "Pop-up Event": "pos"}[cu.true_channel]
        order_plan.append((cu.customer_id, cu.first_order_date, src, None, 1))
    # repeats
    last = cu.first_order_date
    n = 1
    p = REPEAT_P[cu.true_channel]
    while rng.random() < p:
        gap = int(np.clip(rng.lognormal(mean=4.0, sigma=0.55), 12, 240))
        nxt = last + pd.Timedelta(days=gap)
        if nxt > END:
            break
        n += 1
        src, cid = repeat_attribution(nxt)
        order_plan.append((cu.customer_id, nxt, src, cid, n))
        last = nxt
        p = FURTHER_REPEAT_P

order_plan.sort(key=lambda r: r[1])

items_rows, order_rows = [], []
for i, (cid, day, src, camp, n) in enumerate(order_plan):
    order_id = 1001 + i
    ts = day + pd.Timedelta(minutes=int(rng.integers(7 * 60, 24 * 60)))
    live = products[products.launch_date <= day].copy()
    w = live.popularity.astype(float).values
    # new collections sell hard in their first 6 weeks
    fresh = ((day - live.launch_date).dt.days < 42) & (live.collection != "Core")
    w = w * np.where(fresh, 1.8, 1.0)
    if camp in CAMPAIGN_PRODUCT_BOOST:
        w = w * live.sku.map(CAMPAIGN_PRODUCT_BOOST[camp]).fillna(1.0).values
    if day.month in (11, 12, 1, 2):  # cold-weather mix
        w = w * np.where(live.category.isin(["Hoodies", "Crewnecks", "Bottoms"]), 1.3, 1.0)
    if day.month in (6, 7, 8):
        w = w * np.where(live.category.isin(["Hoodies", "Crewnecks"]), 0.6, 1.0)
    w = w / w.sum()
    n_lines = rng.choice([1, 2, 3], p=[0.62, 0.29, 0.09])
    picks = rng.choice(len(live), size=n_lines, replace=False, p=w)
    subtotal = 0.0
    for j in picks:
        pr = live.iloc[j]
        qty = 2 if rng.random() < 0.07 else 1
        size = "OS" if pr.category == "Accessories" else rng.choice(APPAREL_SIZES, p=SIZE_P)
        items_rows.append(dict(order_id=order_id, sku=pr.sku, product_name=pr.product_name,
                               size=size, quantity=qty, unit_price=float(pr.retail_price)))
        subtotal += qty * pr.retail_price

    # discount codes
    code, pct = "", 0.0
    if pd.Timestamp("2024-11-22") <= day <= pd.Timestamp("2024-12-02") and rng.random() < 0.85:
        code, pct = "BFCM25", 0.25
    elif pd.Timestamp("2025-08-15") <= day <= pd.Timestamp("2025-08-31") and rng.random() < 0.5:
        code, pct = "SUMMER20", 0.20
    elif n == 1 and rng.random() < 0.18:
        code, pct = "WELCOME10", 0.10
    elif n > 1 and rng.random() < 0.20:
        code, pct = "VIP15", 0.15
    discount = round(subtotal * pct, 2)
    shipping = 0.0 if (subtotal - discount) >= 75 or src == "pos" else 6.95
    status = "refunded" if rng.random() < 0.03 else "paid"
    order_rows.append(dict(order_id=order_id, customer_id=cid, created_at=ts, financial_status=status,
                           subtotal=round(subtotal, 2), discount_code=code, discount_amount=discount,
                           shipping=shipping, utm_source=src, campaign_id=camp))

orders = pd.DataFrame(order_rows)
items = pd.DataFrame(items_rows)
orders["net_sales"] = orders.subtotal - orders.discount_amount
paid = orders[orders.financial_status == "paid"]

# ---------------------------------------------------------------------------
# 5. Meta Ads spend - backed out from attributed revenue and target ROAS
# ---------------------------------------------------------------------------
attr_rev = paid.groupby("campaign_id").net_sales.sum()
raw_spend = {}
for c in campaigns.itertuples():
    if pd.isna(c.target_roas):
        continue
    noise = rng.normal(1.0, 0.04)
    raw_spend[c.campaign_id] = attr_rev.get(c.campaign_id, 0.0) / (c.target_roas * noise)
# scale so the *overall* ROAS (incl. fixed awareness spend) hits the target
total_attr = attr_rev.sum()
needed_total = total_attr / TARGET_ROAS
scale = (needed_total - AWARENESS_FIXED_SPEND) / sum(raw_spend.values())
spend_total = {k: v * scale for k, v in raw_spend.items()}
spend_total["C09"] = AWARENESS_FIXED_SPEND

purch = (paid.assign(date=paid.created_at.dt.normalize())
         .groupby(["campaign_id", "date"])
         .agg(purchases=("order_id", "count"), purchase_value=("net_sales", "sum")))

ad_rows = []
for c in campaigns.itertuples():
    days = pd.date_range(c.start_date, c.end_date, freq="D")
    w = rng.gamma(shape=6.0, scale=1.0, size=len(days))
    w *= np.array([0.95, 0.95, 0.95, 1.0, 1.05, 1.1, 1.05])[days.dayofweek]
    if c.campaign_id == "C05":  # retargeting budget follows site traffic seasonality
        w *= np.array([MONTH_WEIGHT[m] for m in days.month])
    # ramp up into Black Friday / Cyber Monday
    if c.campaign_id == "C03":
        w *= np.linspace(0.7, 1.6, len(days))
    daily = spend_total[c.campaign_id] * w / w.sum()
    for d, s in zip(days, daily):
        cpm = c.cpm * rng.normal(1.0, 0.08)
        imps = int(round(s / cpm * 1000))
        freq = rng.uniform(1.05, 1.35) if c.strategy != "Retargeting" else rng.uniform(1.6, 2.6)
        reach = int(imps / freq)
        clicks = int(rng.binomial(imps, min(c.ctr * rng.normal(1.0, 0.1), 0.05)))
        link_clicks = int(round(clicks * rng.uniform(0.62, 0.78)))
        lpv = int(round(link_clicks * rng.uniform(0.72, 0.88)))
        p_cnt, p_val = 0, 0.0
        if (c.campaign_id, d) in purch.index:
            p_cnt, p_val = purch.loc[(c.campaign_id, d)]
        atc = max(int(p_cnt), int(rng.binomial(lpv, 0.075 if c.strategy != "Retargeting" else 0.14)))
        ic = max(int(p_cnt), int(round(atc * rng.uniform(0.40, 0.60))))
        ad_rows.append({
            "Reporting starts": d.strftime("%Y-%m-%d"),
            "Reporting ends": d.strftime("%Y-%m-%d"),
            "Campaign ID": f"23851{int(c.campaign_id[1:]):02d}0447{int(c.campaign_id[1:]) * 7:03d}",
            "Campaign name": c.campaign_name,
            "Amount spent (USD)": round(s, 2),
            "Impressions": imps,
            "Reach": reach,
            "Clicks (all)": clicks,
            "Link clicks": link_clicks,
            "Landing page views": lpv,
            "Adds to cart": atc,
            "Checkouts initiated": ic,
            "Purchases": int(p_cnt),
            "Purchases conversion value": round(float(p_val), 2),
        })
ads = pd.DataFrame(ad_rows)

# ---------------------------------------------------------------------------
# 6. Write raw exports, injecting realistic data-quality issues
# ---------------------------------------------------------------------------
cust_lookup = customers.set_index("customer_id")

# --- products.csv ----------------------------------------------------------
prod_out = products.drop(columns=["popularity"]).copy()
prod_out["retail_price"] = prod_out.retail_price.map(lambda v: f"${v:.2f}")
prod_out["launch_date"] = prod_out.launch_date.dt.strftime("%Y-%m-%d")
prod_out.loc[[3, 9], "product_name"] = prod_out.loc[[3, 9], "product_name"] + "  "  # stray spaces
prod_out.to_csv(RAW / "products.csv", index=False)

# --- customers.csv ---------------------------------------------------------
SURVEY_MAP = {  # how the post-purchase survey answer was recorded
    "Meta Ads": ["Instagram Ad", "Facebook Ad", "instagram ad", "Saw an ad on Instagram"],
    "Instagram Organic": ["Instagram (organic)", "Instagram", "IG page"],
    "Referral": ["Friend/Family", "friend", "Word of mouth"],
    "TikTok Organic": ["TikTok", "tiktok"],
    "Pop-up Event": ["Pop-up Event", "Pop up shop"],
}
c_out = customers.copy()
c_out["how_did_you_hear"] = [rng.choice(SURVEY_MAP[ch]) for ch in c_out.true_channel]
c_out.loc[rng.random(len(c_out)) < 0.10, "how_did_you_hear"] = ""  # skipped the survey
c_out["created_at"] = c_out.first_order_date + pd.to_timedelta(rng.integers(0, 60, len(c_out)), "m")
c_out["accepts_marketing"] = np.where(rng.random(len(c_out)) < 0.72, "yes", "no")
mess = rng.random(len(c_out))
c_out.loc[mess < 0.08, "email"] = c_out.loc[mess < 0.08, "email"].str.upper()
c_out.loc[(mess >= 0.08) & (mess < 0.14), "email"] = " " + c_out.loc[(mess >= 0.08) & (mess < 0.14), "email"] + " "
state_names = {"GA": "Georgia", "TX": "Texas", "CA": "California", "NY": "New York", "FL": "Florida"}
idx = c_out.index[(rng.random(len(c_out)) < 0.12) & c_out.state.isin(state_names)]
c_out.loc[idx, "state"] = c_out.loc[idx, "state"].map(state_names)
c_out.loc[rng.random(len(c_out)) < 0.05, "state"] = c_out["state"].str.lower()
c_out.loc[rng.random(len(c_out)) < 0.03, "city"] = ""
c_out = c_out[["customer_id", "first_name", "last_name", "email", "city", "state",
               "created_at", "accepts_marketing", "how_did_you_hear"]]
c_out["created_at"] = c_out.created_at.dt.strftime("%Y-%m-%d %H:%M:%S")
dups = c_out.sample(5, random_state=SEED)
c_out = pd.concat([c_out, dups]).sample(frac=1, random_state=SEED).reset_index(drop=True)
c_out.to_csv(RAW / "customers.csv", index=False)

# --- orders.csv (Shopify style: name '#1001', customer by email) ------------
utm_lookup = campaigns.set_index("campaign_id").utm_campaign
o_out = pd.DataFrame({
    "name": "#" + orders.order_id.astype(str),
    "email": orders.customer_id.map(cust_lookup.email),
    "created_at": orders.created_at.dt.strftime("%Y-%m-%d %H:%M:%S"),
    "financial_status": orders.financial_status,
    "subtotal": orders.subtotal.map(lambda v: f"${v:,.2f}"),
    "discount_code": orders.discount_code,
    "discount_amount": orders.discount_amount,
    "shipping": orders.shipping,
    "total": (orders.subtotal - orders.discount_amount + orders.shipping).map(lambda v: f"${v:,.2f}"),
    "utm_source": orders.utm_source.replace({"pos": "", "direct": ""}),
    "utm_medium": np.where(orders.campaign_id.notna(), "paid_social",
                           np.where(orders.utm_source.isin(["email", "sms"]), orders.utm_source, "")),
    "utm_campaign": orders.campaign_id.map(utm_lookup).fillna(""),
    "source_name": np.where(orders.utm_source == "pos", "pos", "web"),
})
# mixed case utm values and mixed-case emails as typed at checkout
m = rng.random(len(o_out))
o_out.loc[m < 0.10, "utm_campaign"] = o_out.loc[m < 0.10, "utm_campaign"].str.upper()
o_out.loc[(m > 0.95), "email"] = o_out.loc[(m > 0.95), "email"].str.title()
# ~5% of rows exported by a different tool with US date format
us = rng.random(len(o_out)) < 0.05
o_out.loc[us, "created_at"] = pd.to_datetime(o_out.loc[us, "created_at"]).dt.strftime("%m/%d/%Y %H:%M")
# test orders created while setting up the store / payment gateway
tests = pd.DataFrame({
    "name": ["#T-1", "#T-2", "#T-3"], "email": ["test@vederebeyond.com"] * 3,
    "created_at": ["2024-08-30 14:02:11", "2024-08-30 14:20:45", "2025-03-07 10:11:03"],
    "financial_status": ["paid", "voided", "paid"], "subtotal": ["$0.00", "$32.00", "$0.00"],
    "discount_code": ["TEST100", "", "TEST100"], "discount_amount": [0.0, 0.0, 0.0],
    "shipping": [0.0, 0.0, 0.0], "total": ["$0.00", "$32.00", "$0.00"],
    "utm_source": ["", "", ""], "utm_medium": ["", "", ""], "utm_campaign": ["", "", ""],
    "source_name": ["web"] * 3,
})
o_out = pd.concat([o_out, tests, o_out.sample(6, random_state=SEED)], ignore_index=True)
o_out.to_csv(RAW / "orders.csv", index=False)

# --- order_items.csv -------------------------------------------------------
i_out = items.copy()
i_out["order_id"] = "#" + i_out.order_id.astype(str)
zero_lines = i_out.sample(4, random_state=SEED).assign(quantity=0)  # removed-from-cart artifacts
i_out = pd.concat([i_out, zero_lines], ignore_index=True)
i_out.to_csv(RAW / "order_items.csv", index=False)

# --- meta_campaigns.csv ----------------------------------------------------
camp_out = campaigns.copy()
camp_out["meta_campaign_id"] = ads.groupby("Campaign name")["Campaign ID"].first().reindex(
    camp_out.campaign_name).values
camp_out = camp_out[["campaign_id", "meta_campaign_id", "campaign_name", "utm_campaign", "objective",
                     "strategy", "audience", "creative_type", "start_date", "end_date"]]
camp_out["start_date"] = camp_out.start_date.dt.strftime("%Y-%m-%d")
camp_out["end_date"] = camp_out.end_date.dt.strftime("%Y-%m-%d")
camp_out.to_csv(RAW / "meta_campaigns.csv", index=False)

# --- meta_ads_daily.csv (Ads Manager leaves zero conversion cells blank) ----
a_out = ads.copy()
for col in ["Adds to cart", "Checkouts initiated", "Purchases", "Purchases conversion value"]:
    a_out[col] = a_out[col].astype(object)
    a_out.loc[a_out[col] == 0, col] = ""
a_out.to_csv(RAW / "meta_ads_daily.csv", index=False)

# ---------------------------------------------------------------------------
# 7. Calibration report
# ---------------------------------------------------------------------------
net_rev = paid.net_sales.sum()
print("Synthetic data generated ->", RAW.relative_to(ROOT))
print(f"  customers          : {len(customers):,}")
print(f"  orders (paid)      : {len(paid):,}  (+{(orders.financial_status != 'paid').sum()} refunded)")
print(f"  net revenue        : ${net_rev:,.2f}")
print(f"  Meta spend         : ${ads['Amount spent (USD)'].sum():,.2f}")
print(f"  Meta-attrib. rev.  : ${total_attr:,.2f}")
print(f"  overall ROAS       : {total_attr / ads['Amount spent (USD)'].sum():.2f}x")
