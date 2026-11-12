-- =====================================================================
-- Vèdere Beyond analytics database - schema (SQLite)
-- Star-ish model: fact_orders / fact_order_items / fact_ad_daily with
-- customer, product and campaign dimensions.
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_order_lines;
DROP VIEW  IF EXISTS v_campaign_performance;
DROP VIEW  IF EXISTS v_monthly_kpis;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS ad_performance_daily;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS ad_campaigns;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    sku             TEXT NOT NULL UNIQUE,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    collection      TEXT NOT NULL,
    retail_price    REAL NOT NULL,
    unit_cost       REAL NOT NULL,
    launch_date     TEXT NOT NULL,
    unit_margin     REAL NOT NULL,
    margin_pct      REAL NOT NULL
);

CREATE TABLE ad_campaigns (
    campaign_id       TEXT PRIMARY KEY,
    meta_campaign_id  TEXT NOT NULL UNIQUE,
    campaign_name     TEXT NOT NULL,
    utm_campaign      TEXT NOT NULL,
    objective         TEXT NOT NULL,
    strategy          TEXT NOT NULL,
    audience          TEXT,
    creative_type     TEXT,
    start_date        TEXT NOT NULL,
    end_date          TEXT NOT NULL,
    funnel_stage      TEXT NOT NULL
);

CREATE TABLE customers (
    customer_id              TEXT PRIMARY KEY,
    first_name               TEXT,
    last_name                TEXT,
    email                    TEXT NOT NULL UNIQUE,
    city                     TEXT,
    state                    TEXT,
    accepts_marketing        INTEGER,
    acquisition_channel      TEXT NOT NULL,
    acquisition_campaign_id  TEXT REFERENCES ad_campaigns(campaign_id),
    first_order_date         TEXT NOT NULL,
    cohort_month             TEXT NOT NULL,
    total_orders             INTEGER NOT NULL,
    is_repeat_customer       INTEGER NOT NULL,
    lifetime_revenue         REAL NOT NULL,
    lifetime_contribution    REAL NOT NULL,
    last_order_ts            TEXT
);

CREATE TABLE orders (
    order_id               INTEGER PRIMARY KEY,
    customer_id            TEXT NOT NULL REFERENCES customers(customer_id),
    order_ts               TEXT NOT NULL,
    order_date             TEXT NOT NULL,
    order_month            TEXT NOT NULL,
    order_status           TEXT NOT NULL,
    is_refunded            INTEGER NOT NULL,
    customer_order_number  INTEGER NOT NULL,
    is_first_order         INTEGER NOT NULL,
    source_name            TEXT,
    utm_source             TEXT,
    utm_medium             TEXT,
    utm_campaign           TEXT,
    attribution_channel    TEXT NOT NULL,
    campaign_id            TEXT REFERENCES ad_campaigns(campaign_id),
    discount_code          TEXT,
    units                  INTEGER NOT NULL,
    line_count             INTEGER NOT NULL,
    gross_sales            REAL NOT NULL,
    discount               REAL NOT NULL,
    refund_amount          REAL NOT NULL,
    net_sales              REAL NOT NULL,
    shipping_charged       REAL NOT NULL,
    cogs                   REAL NOT NULL,
    fulfillment_cost       REAL NOT NULL,
    payment_fees           REAL NOT NULL,
    contribution_margin    REAL NOT NULL
);

CREATE TABLE order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    sku            TEXT NOT NULL,
    product_name   TEXT NOT NULL,
    size           TEXT,
    quantity       INTEGER NOT NULL,
    unit_price     REAL NOT NULL,
    product_id     TEXT NOT NULL REFERENCES products(product_id),
    unit_cost      REAL NOT NULL,
    line_revenue   REAL NOT NULL,
    line_cogs      REAL NOT NULL
);

CREATE TABLE ad_performance_daily (
    date                 TEXT NOT NULL,
    campaign_id          TEXT NOT NULL REFERENCES ad_campaigns(campaign_id),
    spend                REAL NOT NULL,
    impressions          INTEGER NOT NULL,
    reach                INTEGER NOT NULL,
    clicks               INTEGER NOT NULL,
    link_clicks          INTEGER NOT NULL,
    landing_page_views   INTEGER NOT NULL,
    add_to_cart          INTEGER NOT NULL,
    checkouts_initiated  INTEGER NOT NULL,
    purchases            INTEGER NOT NULL,
    purchase_value       REAL NOT NULL,
    PRIMARY KEY (date, campaign_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_month    ON orders(order_month);
CREATE INDEX idx_orders_campaign ON orders(campaign_id);
CREATE INDEX idx_items_order     ON order_items(order_id);
CREATE INDEX idx_items_product   ON order_items(product_id);
CREATE INDEX idx_ads_campaign    ON ad_performance_daily(campaign_id);
