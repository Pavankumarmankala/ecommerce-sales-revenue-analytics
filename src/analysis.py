"""Sales & revenue analysis — every finding is computed from the orders
frame, nothing is asserted. Planted patterns (see generate_orders.py)
are *detected* by these functions, not passed in.
"""
import pandas as pd

DISCOUNT_BANDS = [(-0.001, 0.0), (0.0, 0.10), (0.10, 0.20), (0.20, 0.30), (0.30, 1.0)]
DISCOUNT_LABELS = ["0%", "1-10%", "11-20%", "21-30%", ">30%"]


def with_month(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df.order_date.dt.to_period("M")
    return df


def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    m = df.groupby("month").agg(orders=("order_id", "count"),
                                 revenue=("revenue", "sum"),
                                 profit=("profit", "sum"),
                                 customers=("customer_id", "nunique")).reset_index()
    m["aov"] = (m.revenue / m.orders).round(2)
    m["mom_revenue_pct"] = (100 * m.revenue.pct_change()).round(2)
    m["margin_pct"] = (100 * m.profit / m.revenue).round(2)
    return m


def category_monthly(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["category", "month"]).agg(
        orders=("order_id", "count"), revenue=("revenue", "sum")).reset_index()


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue by category, with last-6-months vs prior-6-months change —
    the decline detector. Windows are derived from the data's own months."""
    months = sorted(df.month.unique())
    last6, prior6 = months[-6:], months[-12:-6]
    rows = []
    for cat, g in df.groupby("category"):
        last = g[g.month.isin(last6)].revenue.sum()
        prior = g[g.month.isin(prior6)].revenue.sum()
        rows.append({
            "category": cat, "orders": len(g), "revenue": round(g.revenue.sum(), 2),
            "profit": round(g.profit.sum(), 2),
            "margin_pct": round(100 * g.profit.sum() / g.revenue.sum(), 2),
            "revenue_share_pct": 0.0,  # filled below
            "avg_monthly_revenue_prior6": round(prior / 6, 2),
            "avg_monthly_revenue_last6": round(last / 6, 2),
            "change_last6_vs_prior6_pct": round(100 * (last - prior) / prior, 2),
        })
    out = pd.DataFrame(rows)
    out["revenue_share_pct"] = (100 * out.revenue / out.revenue.sum()).round(2)
    return out.sort_values("change_last6_vs_prior6_pct").reset_index(drop=True)


def detect_declining_category(summary: pd.DataFrame) -> pd.Series:
    return summary.iloc[summary.change_last6_vs_prior6_pct.idxmin()]


def product_profitability(df: pd.DataFrame) -> pd.DataFrame:
    p = df.groupby(["product", "category"]).agg(
        orders=("order_id", "count"), units=("quantity", "sum"),
        revenue=("revenue", "sum"), profit=("profit", "sum"),
        avg_discount_pct=("discount_pct", "mean")).reset_index()
    p["margin_pct"] = (100 * p.profit / p.revenue).round(2)
    p["avg_discount_pct"] = (100 * p.avg_discount_pct).round(1)
    return p.sort_values("margin_pct", ascending=False).reset_index(drop=True)


def discount_band_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["discount_band"] = pd.cut(df.discount_pct,
                                 bins=[-0.001, 0.0, 0.10, 0.20, 0.30, 1.0],
                                 labels=DISCOUNT_LABELS)
    b = df.groupby("discount_band", observed=True).agg(
        orders=("order_id", "count"), revenue=("revenue", "sum"),
        profit=("profit", "sum")).reset_index()
    b["margin_pct"] = (100 * b.profit / b.revenue).round(2)
    b["order_share_pct"] = (100 * b.orders / b.orders.sum()).round(2)
    return b


def region_summary(df: pd.DataFrame) -> pd.DataFrame:
    months = sorted(df.month.unique())
    first6, last6 = months[:6], months[-6:]
    rows = []
    for region, g in df.groupby("region"):
        f = g[g.month.isin(first6)].revenue.sum()
        l = g[g.month.isin(last6)].revenue.sum()
        rows.append({
            "region": region, "orders": len(g), "revenue": round(g.revenue.sum(), 2),
            "revenue_share_pct": 0.0,
            "avg_monthly_revenue_first6": round(f / 6, 2),
            "avg_monthly_revenue_last6": round(l / 6, 2),
            "growth_first6_to_last6_pct": round(100 * (l - f) / f, 2),
        })
    out = pd.DataFrame(rows)
    out["revenue_share_pct"] = (100 * out.revenue / out.revenue.sum()).round(2)
    return out.sort_values("growth_first6_to_last6_pct", ascending=False).reset_index(drop=True)


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    s = df.groupby("customer_segment").agg(
        customers=("customer_id", "nunique"), orders=("order_id", "count"),
        revenue=("revenue", "sum"), profit=("profit", "sum")).reset_index()
    s["aov"] = (s.revenue / s.orders).round(2)
    s["orders_per_customer"] = (s.orders / s.customers).round(2)
    s["customer_share_pct"] = (100 * s.customers / s.customers.sum()).round(2)
    s["revenue_share_pct"] = (100 * s.revenue / s.revenue.sum()).round(2)
    return s.sort_values("revenue_share_pct", ascending=False).reset_index(drop=True)


def value_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """Per-customer value tiers by total spend quartile (RFM-lite:
    monetary quartile + orders + recency are all computed per customer)."""
    last_date = df.order_date.max()
    cust = df.groupby("customer_id").agg(
        orders=("order_id", "count"), revenue=("revenue", "sum"),
        last_order=("order_date", "max")).reset_index()
    cust["recency_days"] = (last_date - cust.last_order).dt.days
    cust["tier"] = pd.qcut(cust.revenue, 4,
                           labels=["Bronze", "Silver", "Gold", "Platinum"])
    t = cust.groupby("tier", observed=True).agg(
        customers=("customer_id", "count"), revenue=("revenue", "sum"),
        avg_orders=("orders", "mean"), avg_recency_days=("recency_days", "mean")).reset_index()
    t["revenue_share_pct"] = (100 * t.revenue / t.revenue.sum()).round(2)
    t["avg_orders"] = t.avg_orders.round(2)
    t["avg_recency_days"] = t.avg_recency_days.round(1)
    return t


def top_customers(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    t = df.groupby(["customer_id", "customer_segment", "region"]).agg(
        orders=("order_id", "count"), revenue=("revenue", "sum"),
        profit=("profit", "sum")).reset_index()
    return t.sort_values("revenue", ascending=False).head(n).reset_index(drop=True)


def repeat_customer_stats(df: pd.DataFrame) -> dict:
    per_cust = df.groupby("customer_id").size()
    return {
        "customers_total": int(per_cust.size),
        "repeat_customers": int((per_cust >= 2).sum()),
        "repeat_rate_pct": round(100 * float((per_cust >= 2).mean()), 2),
    }


def compute_opportunities(df: pd.DataFrame, products: pd.DataFrame,
                          declining: pd.Series, segments: pd.DataFrame) -> list:
    """Each opportunity carries the computed number behind it."""
    opps = []

    # 1 — Cap discounts at 20% on negative-margin products: recompute profit
    neg_products = products.loc[products.margin_pct < 0, "product"].tolist()
    neg_orders = df[df["product"].isin(neg_products)]
    capped_profit = (neg_orders.quantity * neg_orders.unit_price * 0.80
                     - neg_orders.quantity * neg_orders.unit_cost)
    recovery = float(capped_profit.sum() - neg_orders.profit.sum())
    current_loss = float(neg_orders.profit.sum())
    opps.append({
        "opportunity": "Cap discounts at 20% on negative-margin promo products "
                       f"({', '.join(neg_products)})",
        "basis": f"These products lost ${abs(current_loss):,.0f} over 24 months at "
                 f"current 35-55% promo discounts",
        "computed_impact": round(recovery, 2),
        "impact_label": "profit recoverable over 24 months if discount capped at 20%, same volumes",
    })

    # 2 — Restore the declining category to its prior-6-month run rate
    monthly_gap = float(declining.avg_monthly_revenue_prior6 - declining.avg_monthly_revenue_last6)
    opps.append({
        "opportunity": f"Reverse the {declining.category} decline "
                       f"({declining.change_last6_vs_prior6_pct}% last 6 vs prior 6 months)",
        "basis": f"Average monthly revenue fell from ${declining.avg_monthly_revenue_prior6:,.0f} "
                 f"to ${declining.avg_monthly_revenue_last6:,.0f}",
        "computed_impact": round(monthly_gap * 12, 2),
        "impact_label": "annual revenue recoverable at the prior-6-month run rate",
    })

    # 3 — Lift Occasional customers toward Regular AOV
    reg = segments[segments.customer_segment == "Regular"].iloc[0]
    occ = segments[segments.customer_segment == "Occasional"].iloc[0]
    aov_gap = float(reg.aov - occ.aov)
    potential = aov_gap * int(occ.orders)
    opps.append({
        "opportunity": "Lift Occasional-segment basket size toward the Regular-segment AOV "
                       "(bundles, free-shipping threshold, second-item offers)",
        "basis": f"Occasional AOV is ${occ.aov:,.2f} vs Regular ${reg.aov:,.2f} "
                 f"across {int(occ.orders):,} Occasional orders",
        "computed_impact": round(potential, 2),
        "impact_label": "revenue upside over 24 months if Occasional AOV matched Regular AOV",
    })
    return opps
