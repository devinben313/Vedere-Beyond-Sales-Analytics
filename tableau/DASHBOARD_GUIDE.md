# Tableau Dashboard — Build Guide

This guide builds the **Vèdere Beyond Sales & Marketing Dashboard** in Tableau Desktop or Tableau Public from the extracts in `tableau/data/`. Running `python scripts/05_export_tableau.py` regenerates them.

A static preview of the target layout is in [`reports/figures/dashboard_preview.png`](../reports/figures/dashboard_preview.png).

---

## 1. Data sources

| File | Grain | Used for |
|---|---|---|
| `vb_orders.csv` | 1 row per order (incl. refunded) | Revenue trend, AOV, new vs returning, discounts, KPIs |
| `vb_order_lines.csv` | 1 row per non-refunded order line | Product & category profitability |
| `vb_ad_performance_daily.csv` | campaign × day | Spend, ROAS, CTR, CPM, funnel |
| `vb_customers.csv` | 1 row per customer (no PII) | Channel mix, LTV, repeat rate |
| `vb_monthly_kpis.csv` | month | Pre-aggregated KPI trend, CAC |
| `vb_cohort_retention.csv` | cohort × months since first order | Retention heatmap |
| `vb_campaign_scorecard.csv` | campaign | ROAS ranking + Scale / Optimize / Cut action |
| `vb_product_margins.csv` | product | Product margin table |
| `vb_budget_reallocation.csv` | campaign strategy | Current vs proposed budget |

**Relationships** (Data Source tab, use *relationships*, not joins):

- `vb_orders.customer_id` → `vb_customers.customer_id`
- `vb_orders.order_id` → `vb_order_lines.order_id`
- `vb_ad_performance_daily.campaign_id` → `vb_campaign_scorecard.campaign_id`

Keep `vb_monthly_kpis`, `vb_cohort_retention` and `vb_budget_reallocation` as separate data sources. To filter ad data and order data by the same date, blend them on **Month** (`DATETRUNC('month', [Order Date])` ↔ `DATETRUNC('month', [Date])`).

Set `order_date`, `date` and `first_order_date` to **Date** type; set `is_refunded`, `is_first_order` and `is_repeat_customer` to **Boolean** (or keep them as 0/1 integers).

---

## 2. Calculated fields

```text
// ---------- vb_orders ----------
[Net Revenue]            = SUM(IF NOT [Is Refunded] THEN [Net Sales] END)
[Orders]                 = COUNTD(IF NOT [Is Refunded] THEN [Order Id] END)
[AOV]                    = [Net Revenue] / [Orders]
[Gross Profit]           = SUM([Net Sales] - [Cogs])
[Gross Margin %]         = [Gross Profit] / SUM([Net Sales])
[Contribution Margin]    = SUM([Contribution Margin])
[New Customer Revenue]   = SUM(IF [Is First Order] AND NOT [Is Refunded] THEN [Net Sales] END)
[Returning Revenue]      = SUM(IF NOT [Is First Order] AND NOT [Is Refunded] THEN [Net Sales] END)
[Returning Revenue %]    = [Returning Revenue] / [Net Revenue]
[Meta Attributed Rev]    = SUM(IF NOT ISNULL([Campaign Id]) AND NOT [Is Refunded] THEN [Net Sales] END)
[Discount Rate]          = SUM([Discount]) / SUM([Gross Sales])

// ---------- vb_customers ----------
[Customers]              = COUNTD([Customer Id])
[Repeat Purchase Rate]   = SUM(IIF([Is Repeat Customer], 1, 0)) / COUNTD([Customer Id])
[Avg LTV (Contribution)] = AVG([Lifetime Contribution])

// ---------- vb_ad_performance_daily ----------
[Spend]                  = SUM([Spend])
[ROAS]                   = SUM([Purchase Value]) / SUM([Spend])
[CPM]                    = SUM([Spend]) / SUM([Impressions]) * 1000
[Link CTR]               = SUM([Link Clicks]) / SUM([Impressions])
[CPC]                    = SUM([Spend]) / SUM([Link Clicks])
[Cost per Purchase]      = SUM([Spend]) / SUM([Purchases])
[LPV to Purchase %]      = SUM([Purchases]) / SUM([Landing Page Views])
[Break-even ROAS]        = 1.63        // parameter: 1 / contribution-margin rate on ad-driven orders
[ROAS vs Break-even]     = IF [ROAS] >= 3 THEN "Scale"
                           ELSEIF [ROAS] >= 1.25 * [Break-even ROAS] THEN "Optimize & maintain"
                           ELSE "Cut / restructure" END

// ---------- vb_monthly_kpis ----------
[Blended CAC]            = SUM([Ad Spend]) / SUM([New Customers])   // paid (Meta-only) CAC: reports/query_results/03_customer_acquisition_cost.csv
[Profit After Ads]       = SUM([Profit After Ads])

// ---------- vb_order_lines ----------
[Product Net Revenue]    = SUM([Net Line Revenue])
[Product Gross Profit]   = SUM([Net Line Revenue] - [Line Cogs])
[Product Margin %]       = [Product Gross Profit] / [Product Net Revenue]
```

Create a **parameter** `p_BreakEvenROAS` (float, default 1.63) and use it in place of the constant, so the reference line can be changed to test other cost assumptions.

---

## 3. Worksheets

| # | Sheet | Build |
|---|---|---|
| 1 | **KPI – BANs** | Six text tiles: Net Revenue, Customers, Meta ROAS, Paid CAC ($32.55), Repeat Purchase Rate, Gross Margin %. One sheet per tile, or one sheet with Measure Names on Columns. |
| 2 | **Revenue Trend** | Columns `MONTH(Order Date)`; Rows `[New Customer Revenue]` and `[Returning Revenue]` as a stacked bar (Measure Values, Color = Measure Names: blue = new, orange = returning). |
| 3 | **Spend & ROAS by Month** | Two separate panes, *not* dual-axis: bar of `[Spend]` by `MONTH(Date)`, and line of `[ROAS]` by month with a reference line at `p_BreakEvenROAS`. |
| 4 | **Campaign ROAS** | Rows `Campaign Name`, sorted by `[ROAS]` descending; Columns `[ROAS]`; Color = `[ROAS vs Break-even]` (Scale = blue, Optimize = gray, Cut = red); reference line at break-even; label = ROAS. Tooltip: spend, revenue, CPA, CTR, CPM. |
| 5 | **Spend vs Revenue Share** | Rows `Strategy`; side-by-side bars of `% of total Spend` and `% of total Purchase Value` (quick table calc: percent of total). |
| 6 | **Ad Funnel** | Rows `Strategy`; Columns Impressions → Link Clicks → LPV → Add to Cart → Purchases, shown as rates (CTR, LPV→ATC, ATC→Purchase), as a highlight table. |
| 7 | **CAC Trend** | `vb_monthly_kpis` or `03_customer_acquisition_cost` output: line of paid and blended CAC by month. |
| 8 | **Channel Value** | `vb_customers`: Rows `Acquisition Channel`; bars of `[Avg LTV (Contribution)]` and `[Repeat Purchase Rate]`. |
| 9 | **Cohort Retention** | `vb_cohort_retention`: Rows `Cohort Month`, Columns `Months Since First` (filter out 0), Color = `AVG(Retention Pct)`, single-hue blue sequential, label the value. |
| 10 | **Product Profitability** | `vb_order_lines`: Rows `Product Name` sorted by `[Product Gross Profit]`; bars, label = profit and margin %; color top 3 blue, margin < 60% red. |
| 11 | **Volume vs Margin** | Scatter: Columns `SUM(Quantity)`, Rows `[Product Margin %]`, Size = `[Product Net Revenue]`, Detail = Product Name. |
| 12 | **Budget Reallocation** | `vb_budget_reallocation`: Rows `Strategy`; side-by-side bars `Current Budget` vs `Proposed Budget`; label `Budget Change`. |

**Colors** (consistent across sheets): New / primary series `#2a78d6`, Returning / second series `#eb6834`, neutral `#b8b6ae`, cut / below break-even `#d03b3b`. Gridlines light gray, no chart borders.

---

## 4. Dashboards

### Dashboard 1 — Executive Overview (1400 × 900)
```
┌──────────────────────────────────────────────────────────────────────────┐
│ Title · date-range filter · Acquisition Channel filter · Category filter │
├────────┬────────┬────────┬────────┬────────┬─────────────────────────────┤
│Revenue │Customers│ ROAS  │Paid CAC│Repeat %│ Gross margin               │  ← KPI BANs
├────────────────────────────────────┬─────────────────────────────────────┤
│ Revenue Trend (new vs returning)   │ Campaign ROAS vs break-even         │
├───────────────────┬────────────────┴──────┬──────────────────────────────┤
│ CAC Trend         │ Cumulative repeat rate│ Top products by gross profit │
└───────────────────┴───────────────────────┴──────────────────────────────┘
```

### Dashboard 2 — Advertising Performance
Spend & ROAS by month · Campaign ROAS · Spend vs revenue share · Ad funnel · Budget reallocation.
**Action:** clicking a campaign in *Campaign ROAS* filters the monthly spend/ROAS panes (Dashboard → Actions → Filter).

### Dashboard 3 — Customers & Products
Channel value · Cohort retention heatmap · Product profitability · Volume vs margin.
**Action:** selecting a category highlights its products in both product views.

**Filters** (one row, top of each dashboard, applied to all worksheets using related sources): Order Month range, Acquisition Channel, Product Category, Campaign Strategy.

---

## 5. Publishing

1. *File → Save to Tableau Public As…* (Tableau Public) or *Server → Publish Workbook* (Tableau Cloud).
2. With CSV sources, Tableau Public stores an extract automatically. On Tableau Desktop, choose *Extract* in the Data Source tab before publishing.
3. Save a packaged workbook as `tableau/vedere_beyond_dashboard.twbx` and commit it next to this guide.

> **Note:** a `.twbx` cannot be generated by script; it is built in Tableau from these extracts. Every number on the dashboard can be checked against `reports/query_results/`.
