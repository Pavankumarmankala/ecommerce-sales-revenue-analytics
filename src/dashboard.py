"""Builds chart PNGs and a self-contained HTML dashboard from gold data."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "data" / "gold"; OUT = ROOT / "outputs"; CHARTS = OUT / "charts"


def build():
    CHARTS.mkdir(parents=True, exist_ok=True)
    monthly = pd.read_csv(GOLD / "monthly_revenue.csv")
    monthly["month"] = pd.PeriodIndex(monthly["month"], freq="M").to_timestamp()
    cat_monthly = pd.read_csv(GOLD / "category_monthly.csv")
    cat_monthly["month"] = pd.PeriodIndex(cat_monthly["month"], freq="M").to_timestamp()
    products = pd.read_csv(GOLD / "product_profitability.csv")
    bands = pd.read_csv(GOLD / "discount_band_summary.csv")
    regions = pd.read_csv(GOLD / "region_summary.csv")
    metrics = json.loads((OUT / "metrics.json").read_text())

    # 1 — monthly revenue trend
    plt.figure(figsize=(11, 3.8))
    plt.plot(monthly.month, monthly.revenue, marker="o", ms=3)
    plt.title("Monthly revenue trend (24 months)"); plt.ylabel("Revenue ($)")
    plt.tight_layout(); plt.savefig(CHARTS / "monthly_revenue_trend.png", dpi=150); plt.close()

    # 2 — category trend, declining category highlighted
    plt.figure(figsize=(11, 4.2))
    pivot = cat_monthly.pivot(index="month", columns="category", values="revenue")
    for col in pivot.columns:
        if col == metrics["declining_category"]:
            plt.plot(pivot.index, pivot[col], color="red", lw=2.5, label=f"{col} (declining)")
        else:
            plt.plot(pivot.index, pivot[col], lw=1.2, alpha=.75, label=col)
    plt.legend(); plt.title("Monthly revenue by category"); plt.ylabel("Revenue ($)")
    plt.tight_layout(); plt.savefig(CHARTS / "category_trend.png", dpi=150); plt.close()

    # 3 — profit margin by product
    p = products.sort_values("margin_pct")
    colors = ["red" if v < 0 else "steelblue" for v in p.margin_pct]
    plt.figure(figsize=(8.5, 6.5))
    plt.barh(p["product"], p.margin_pct, color=colors)
    plt.axvline(0, color="black", lw=.8)
    plt.title("Profit margin % by product (red = losing money)"); plt.xlabel("Margin %")
    plt.tight_layout(); plt.savefig(CHARTS / "product_margin.png", dpi=150); plt.close()

    # 4 — discount band vs margin
    plt.figure(figsize=(7.5, 3.8))
    plt.bar(bands.discount_band.astype(str), bands.margin_pct,
            color=["green" if v >= 0 else "red" for v in bands.margin_pct])
    plt.axhline(0, color="black", lw=.8)
    plt.title("Average profit margin % by discount band"); plt.ylabel("Margin %")
    plt.tight_layout(); plt.savefig(CHARTS / "discount_band_margin.png", dpi=150); plt.close()

    # 5 — region growth (first 6 vs last 6 avg monthly revenue)
    r = regions.sort_values("growth_first6_to_last6_pct")
    plt.figure(figsize=(7.5, 3.8))
    plt.barh(r.region, r.growth_first6_to_last6_pct, color="teal")
    plt.title("Region revenue growth % (avg monthly, first 6 vs last 6 months)")
    plt.tight_layout(); plt.savefig(CHARTS / "region_growth.png", dpi=150); plt.close()

    findings = ""
    findings_path = OUT / "findings.md"
    if findings_path.exists():
        findings = ("<h2>Findings</h2><pre style='white-space:pre-wrap;background:#fff;"
                    "border:1px solid #ddd;border-radius:8px;padding:16px'>"
                    + findings_path.read_text().replace("<", "&lt;") + "</pre>")
    cards = "".join(
        f"<div class='card'><h3>{k.replace('_', ' ').title()}</h3><p>{v}</p></div>"
        for k, v in metrics.items() if isinstance(v, (int, float, str)))
    html = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>E-Commerce Sales &amp; Revenue Analytics</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;background:#f7f7f9}}
.card{{display:inline-block;background:#fff;border:1px solid #ddd;border-radius:8px;
padding:12px 16px;margin:6px;min-width:170px}} img{{max-width:100%;background:#fff;
border:1px solid #ddd;border-radius:8px;margin:8px 0}}</style></head><body>
<h1>E-Commerce Sales &amp; Revenue Analytics</h1>{cards}
<h2>Monthly revenue</h2><img src='charts/monthly_revenue_trend.png'>
<h2>Category trend</h2><img src='charts/category_trend.png'>
<h2>Product margin</h2><img src='charts/product_margin.png'>
<h2>Discount band vs margin</h2><img src='charts/discount_band_margin.png'>
<h2>Region growth</h2><img src='charts/region_growth.png'>
{findings}</body></html>"""
    (OUT / "dashboard.html").write_text(html)
    print("dashboard + 5 charts written to", OUT)


if __name__ == "__main__":
    build()
