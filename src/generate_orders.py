"""Synthetic e-commerce orders generator — 24 months of orders.

Seeded (seed=42) so every finding in this project is reproducible, and
with DELIBERATELY PLANTED patterns so the analysis can be verified
against ground truth:

  1. DECLINING CATEGORY — "Home & Kitchen" order weight decays steeply
     over the last 6 months (months 19-24, Jul-Dec 2025), multiplier
     0.78 -> 0.64 -> 0.52 -> 0.42 -> 0.34 -> 0.28. (Steep, because the
     last-6 window contains the Nov/Dec seasonal spike, which would
     otherwise mask a gentle decline in revenue terms.) All other
     categories are flat or growing (Electronics grows ~15%).
  2. GROWING REGION — customers in the "West" region are sampled with a
     weight that rises linearly from 1.0x to 1.9x across the 24 months,
     so West order/revenue share grows steadily.
  3. DISCOUNT-DRIVEN NEGATIVE PROFIT — three "promo" products
     (Fitness Tracker, Mechanical Keyboard, Hair Dryer) carry low base
     margins (28-30%) but are discounted 35-55% on ~80% of orders. Since profit
     per unit = price x (margin - discount), these products lose money
     on most discounted orders. Other products are discounted 0-25%.
  4. HIGH-VALUE SEGMENT — "Premium" customers are only ~8% of the
     customer base but are sampled ~3.2x as often and buy larger
     baskets, so they should account for a disproportionate share
     of revenue (analysis verifies the exact share).

Profit definition: revenue = qty x unit_price x (1 - discount_pct);
profit = revenue - qty x unit_cost, where unit_cost is NOT discounted
(the discount comes out of the seller's margin, as in real retail).
"""
import numpy as np
import pandas as pd

# product: (category, unit_price, base_margin_pct, is_promo)
PRODUCTS = {
    "Wireless Headphones":    ("Electronics",    129.99, 0.32, False),
    "Smart Speaker":          ("Electronics",     89.99, 0.30, False),
    "Laptop Stand":           ("Electronics",     49.99, 0.38, False),
    "Mechanical Keyboard":    ("Electronics",    119.99, 0.28, True),
    "Running Shoes":          ("Apparel",        109.99, 0.36, False),
    "Denim Jacket":           ("Apparel",         79.99, 0.40, False),
    "Yoga Leggings":          ("Apparel",         59.99, 0.42, False),
    "Graphic T-Shirt":        ("Apparel",         29.99, 0.45, False),
    "Air Fryer":              ("Home & Kitchen", 139.99, 0.26, False),
    "Ceramic Dinnerware Set": ("Home & Kitchen",  69.99, 0.34, False),
    "Robot Vacuum":           ("Home & Kitchen", 249.99, 0.22, False),
    "Scented Candle Set":     ("Home & Kitchen",  34.99, 0.48, False),
    "Vitamin C Serum":        ("Beauty",          39.99, 0.52, False),
    "Electric Toothbrush":    ("Beauty",          74.99, 0.33, False),
    "Hair Dryer":             ("Beauty",          89.99, 0.30, True),
    "Skincare Gift Set":      ("Beauty",          99.99, 0.44, False),
    "Adjustable Dumbbells":   ("Sports",         199.99, 0.27, False),
    "Camping Tent":           ("Sports",         159.99, 0.31, False),
    "Fitness Tracker":        ("Sports",          99.99, 0.29, True),
    "Insulated Water Bottle": ("Sports",          24.99, 0.50, False),
    "Building Block Set":     ("Toys",            59.99, 0.37, False),
    "Board Game":             ("Toys",            44.99, 0.40, False),
    "RC Car":                 ("Toys",            79.99, 0.30, False),
    "Plush Toy":              ("Toys",            19.99, 0.55, False),
}
CATEGORIES = ["Electronics", "Apparel", "Home & Kitchen", "Beauty", "Sports", "Toys"]
CATEGORY_WEIGHTS = np.array([0.24, 0.20, 0.18, 0.13, 0.14, 0.11])
DECLINING_CATEGORY = "Home & Kitchen"
GROWING_REGION = "West"
REGIONS = ["Northeast", "Midwest", "South", "West"]
SEGMENTS = ["Premium", "Regular", "Occasional"]
SEGMENT_FREQ_WEIGHT = {"Premium": 3.2, "Regular": 1.0, "Occasional": 0.4}
SEGMENT_QTY_LAMBDA = {"Premium": 1.8, "Regular": 0.8, "Occasional": 0.4}
SEASONALITY = {1: .92, 2: .90, 3: .98, 4: 1.00, 5: 1.02, 6: 1.00,
               7: .98, 8: 1.00, 9: 1.03, 10: 1.08, 11: 1.25, 12: 1.35}
CHANNELS = ["Online", "Mobile App", "Marketplace"]


def _catalogue() -> pd.DataFrame:
    rows = [{"product": p, "category": c, "unit_price": price,
             "unit_cost": round(price * (1 - margin), 2), "is_promo": promo}
            for p, (c, price, margin, promo) in PRODUCTS.items()]
    return pd.DataFrame(rows)


def generate(n_customers: int = 12_000, months: int = 24,
             base_monthly_orders: int = 1_900, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2024-01-01")
    catalogue = _catalogue()
    by_category = {c: catalogue[catalogue.category == c] for c in CATEGORIES}

    customers = pd.DataFrame({
        "customer_id": [f"CUST-{i:05d}" for i in range(n_customers)],
        "region": rng.choice(REGIONS, n_customers, p=[.24, .21, .33, .22]),
        "customer_segment": rng.choice(SEGMENTS, n_customers, p=[.08, .57, .35]),
    })
    customers["freq_weight"] = customers.customer_segment.map(SEGMENT_FREQ_WEIGHT)

    frames = []
    order_counter = 0
    for m in range(months):
        month_start = start + pd.DateOffset(months=m)
        n = int(base_monthly_orders * (1 + 0.006 * m) * SEASONALITY[month_start.month])

        # PLANTED PATTERN 2 — West customers sampled up to 1.9x by month 24
        weights = customers.freq_weight.values.copy()
        west_factor = 1.0 + 0.9 * (m / (months - 1))
        weights[customers.region.values == GROWING_REGION] *= west_factor
        cust_idx = rng.choice(n_customers, n, p=weights / weights.sum())
        picked = customers.iloc[cust_idx].reset_index(drop=True)

        # PLANTED PATTERN 1 — Home & Kitchen weight decays in last 6 months
        decline_multipliers = [0.78, 0.64, 0.52, 0.42, 0.34, 0.28]
        cat_w = CATEGORY_WEIGHTS.copy()
        if m >= months - 6:
            cat_w[CATEGORIES.index(DECLINING_CATEGORY)] *= decline_multipliers[m - (months - 6)]
        cat_w[CATEGORIES.index("Electronics")] *= 1 + 0.15 * (m / (months - 1))
        cat_names = rng.choice(CATEGORIES, n, p=cat_w / cat_w.sum())

        prod_name = np.empty(n, dtype=object)
        prod_price = np.zeros(n); prod_cost = np.zeros(n); prod_promo = np.zeros(n, dtype=bool)
        for c in CATEGORIES:
            mask = cat_names == c
            if not mask.any():
                continue
            sub = by_category[c]
            choice = rng.choice(len(sub), mask.sum())
            prod_name[mask] = sub["product"].values[choice]
            prod_price[mask] = sub["unit_price"].values[choice]
            prod_cost[mask] = sub["unit_cost"].values[choice]
            prod_promo[mask] = sub["is_promo"].values[choice]

        qty_lambda = picked.customer_segment.map(SEGMENT_QTY_LAMBDA).values
        quantity = np.clip(rng.poisson(qty_lambda) + 1, 1, 7)
        unit_price = np.round(prod_price * rng.lognormal(0, 0.03, n), 2)

        # PLANTED PATTERN 3 — promo products discounted 35-55% most of the time
        discount = rng.choice([0.0, 0.05, 0.10, 0.15, 0.20, 0.25], n,
                              p=[.50, .19, .14, .09, .05, .03])
        promo_mask = prod_promo & (rng.random(n) < 0.80)
        discount[promo_mask] = np.round(rng.uniform(0.35, 0.55, promo_mask.sum()), 2)

        days = month_start.days_in_month
        timestamps = month_start + pd.to_timedelta(
            rng.integers(0, days * 86400, n), unit="s")

        revenue = np.round(quantity * unit_price * (1 - discount), 2)
        profit = np.round(revenue - quantity * prod_cost, 2)
        frames.append(pd.DataFrame({
            "order_id": [f"ORD-{order_counter + i + 1:06d}" for i in range(n)],
            "order_date": timestamps,
            "customer_id": picked.customer_id.values,
            "customer_segment": picked.customer_segment.values,
            "region": picked.region.values,
            "category": cat_names,
            "product": prod_name,
            "sales_channel": rng.choice(CHANNELS, n, p=[.50, .32, .18]),
            "quantity": quantity,
            "unit_price": unit_price,
            "unit_cost": np.round(prod_cost, 2),
            "discount_pct": np.round(discount, 2),
            "revenue": revenue,
            "profit": profit,
        }))
        order_counter += n

    df = pd.concat(frames, ignore_index=True).sort_values("order_date").reset_index(drop=True)
    df["order_id"] = [f"ORD-{i + 1:06d}" for i in range(len(df))]
    return df


if __name__ == "__main__":
    out = generate()
    print(out.shape)
    print(out.groupby(out.order_date.dt.to_period("M")).size().describe())
