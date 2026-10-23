import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from generate_orders import generate, DECLINING_CATEGORY, PRODUCTS
from analysis import (with_month, category_summary, detect_declining_category,
                      discount_band_summary, segment_summary, product_profitability)


@pytest.fixture(scope="module")
def df():
    return with_month(generate())


def test_dataset_shape_and_coverage(df):
    assert 40_000 <= len(df) <= 60_000
    assert df.month.nunique() == 24
    assert df.order_id.is_unique
    assert df[["customer_id", "category", "product", "region"]].notna().all().all()


def test_money_math_is_consistent(df):
    expected_revenue = df.quantity * df.unit_price * (1 - df.discount_pct)
    assert np.allclose(df.revenue, expected_revenue, atol=0.05)
    expected_profit = df.revenue - df.quantity * df.unit_cost
    assert np.allclose(df.profit, expected_profit, atol=0.05)


def test_products_match_catalogue(df):
    assert set(df["product"]) == set(PRODUCTS)
    assert set(df["category"]) == {c for c, *_ in PRODUCTS.values()}


def test_planted_declining_category_is_detected(df):
    summary = category_summary(df)
    detected = detect_declining_category(summary)
    assert detected.category == DECLINING_CATEGORY
    # a real decline, not noise
    assert detected.change_last6_vs_prior6_pct < -20


def test_discount_tradeoff(df):
    bands = discount_band_summary(df)
    margin = {str(r.discount_band): r.margin_pct for r in bands.itertuples()}
    assert margin[">30%"] < margin["0%"]
    assert margin[">30%"] < 0  # deep-discount orders lose money on average


def test_planted_promo_products_are_the_negative_margin_ones(df):
    products = product_profitability(df)
    negative = set(products[products.margin_pct < 0]["product"])
    planted_promo = {p for p, (*_, promo) in PRODUCTS.items() if promo}
    assert negative == planted_promo


def test_premium_segment_punches_above_its_weight(df):
    segments = segment_summary(df)
    premium = segments[segments.customer_segment == "Premium"].iloc[0]
    assert premium.revenue_share_pct > 2 * premium.customer_share_pct
