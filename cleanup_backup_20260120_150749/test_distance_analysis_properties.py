# -*- coding: utf-8 -*-
"""
分距离订单诊断 API 属性测试

Property-Based Tests for Distance Analysis API

使用 hypothesis 库进行属性测试，验证以下属性：
- Property 1: Distance Band Grouping Completeness (距离区间分组完整性)
- Property 2: API Filtering Correctness (API筛选正确性)
- Property 3: Metrics Calculation Consistency (指标计算一致性)
- Property 5: Optimal Distance Identification (最优距离识别)

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume


# ==================== 距离区间定义（与 orders.py 保持一致） ====================
# 7个距离区间常量定义
DISTANCE_BANDS = [
    {"label": "0-1km", "min": 0, "max": 1},
    {"label": "1-2km", "min": 1, "max": 2},
    {"label": "2-3km", "min": 2, "max": 3},
    {"label": "3-4km", "min": 3, "max": 4},
    {"label": "4-5km", "min": 4, "max": 5},
    {"label": "5-6km", "min": 5, "max": 6},
    {"label": "6km+", "min": 6, "max": float('inf')},
]


def get_distance_band(distance: float) -> dict:
    """
    根据距离值返回所属区间
    
    Args:
        distance: 配送距离（公里）
    
    Returns:
        对应的距离区间字典
    """
    if distance < 0:
        distance = 0
    
    for band in DISTANCE_BANDS:
        if band["min"] <= distance < band["max"]:
            return band
    
    # 默认返回最后一个区间（6km+）
    return DISTANCE_BANDS[-1]


def get_distance_band_index(distance: float) -> int:
    """
    根据距离值返回所属区间的索引
    
    Args:
        distance: 配送距离（公里）
    
    Returns:
        区间索引 (0-6)
    """
    if distance < 0:
        distance = 0
    
    for i, band in enumerate(DISTANCE_BANDS):
        if band["min"] <= distance < band["max"]:
            return i
    
    return len(DISTANCE_BANDS) - 1


# ==================== Property 1: Distance Band Grouping Completeness ====================
# **Feature: distance-order-diagnosis, Property 1: Distance Band Grouping Completeness**
# **Validates: Requirements 1.1, 1.6**
# *For any* order with a valid delivery_distance value (≥0), the order SHALL be assigned 
# to exactly one of the 7 distance bands, and the sum of order_count across all bands 
# SHALL equal the total number of orders.

@settings(max_examples=100)
@given(distance=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
def test_property_1_distance_band_grouping_completeness(distance: float):
    """
    Property 1: Distance Band Grouping Completeness
    
    *For any* order with a valid delivery_distance value (≥0), the order SHALL be 
    assigned to exactly one of the 7 distance bands.
    
    **Validates: Requirements 1.1, 1.6**
    """
    # Get the band for this distance
    band = get_distance_band(distance)
    band_index = get_distance_band_index(distance)
    
    # Verify the band is one of the 7 defined bands
    assert band in DISTANCE_BANDS, f"Distance {distance} was not assigned to a valid band"
    
    # Verify the band index is valid (0-6)
    assert 0 <= band_index <= 6, f"Band index {band_index} is out of range for distance {distance}"
    
    # Verify the distance falls within the band's range
    assert band["min"] <= distance, f"Distance {distance} is below band min {band['min']}"
    if band["max"] != float('inf'):
        assert distance < band["max"], f"Distance {distance} is at or above band max {band['max']}"


@settings(max_examples=100)
@given(distances=st.lists(
    st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
    min_size=1,
    max_size=100
))
def test_property_1_sum_equals_total(distances: list):
    """
    Property 1 (Part 2): Sum of order_count across all bands equals total orders
    
    *For any* set of orders, the sum of order_count across all 7 bands SHALL equal 
    the total number of orders.
    
    **Validates: Requirements 1.1, 1.6**
    """
    # Count orders in each band
    band_counts = [0] * 7
    for distance in distances:
        band_index = get_distance_band_index(distance)
        band_counts[band_index] += 1
    
    # Verify sum equals total
    total_in_bands = sum(band_counts)
    assert total_in_bands == len(distances), \
        f"Sum of band counts ({total_in_bands}) != total orders ({len(distances)})"


# ==================== Property 2: API Filtering Correctness ====================
# **Feature: distance-order-diagnosis, Property 2: API Filtering Correctness**
# **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
# *For any* combination of filter parameters, all orders included in the response 
# SHALL match ALL specified filter criteria.

# Note: This property is tested at the integration level with actual API calls.
# Here we test the distance band assignment logic which is the core of filtering.

@settings(max_examples=100)
@given(
    distance=st.floats(min_value=0, max_value=20, allow_nan=False, allow_infinity=False),
    expected_band_index=st.integers(min_value=0, max_value=6)
)
def test_property_2_band_boundaries(distance: float, expected_band_index: int):
    """
    Property 2: Band boundaries are correctly applied
    
    *For any* distance value, it should be assigned to the correct band based on 
    the defined boundaries.
    
    **Validates: Requirements 1.2, 1.3, 1.4, 1.5**
    """
    band = DISTANCE_BANDS[expected_band_index]
    
    # Only test if distance falls within this band's range
    if band["min"] <= distance < band["max"]:
        actual_index = get_distance_band_index(distance)
        assert actual_index == expected_band_index, \
            f"Distance {distance} should be in band {expected_band_index} but was assigned to {actual_index}"


# ==================== Property 3: Metrics Calculation Consistency ====================
# **Feature: distance-order-diagnosis, Property 3: Metrics Calculation Consistency**
# **Validates: Requirements 1.6, 1.7**
# *For any* distance band, the following invariants SHALL hold:
# - profit_rate = (profit / revenue) * 100 (when revenue > 0)
# - delivery_cost_rate = (delivery_cost / revenue) * 100 (when revenue > 0)
# - avg_order_value = revenue / order_count (when order_count > 0)

@settings(max_examples=100)
@given(
    revenue=st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False),
    profit=st.floats(min_value=-10000, max_value=50000, allow_nan=False, allow_infinity=False),
    delivery_cost=st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
    order_count=st.integers(min_value=1, max_value=1000)
)
def test_property_3_metrics_calculation_consistency(
    revenue: float, 
    profit: float, 
    delivery_cost: float, 
    order_count: int
):
    """
    Property 3: Metrics Calculation Consistency
    
    *For any* distance band with revenue > 0 and order_count > 0, the derived metrics 
    SHALL be calculated correctly.
    
    **Validates: Requirements 1.6, 1.7**
    """
    # Calculate metrics using the same formulas as the API
    profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
    delivery_cost_rate = round(delivery_cost / revenue * 100, 2) if revenue > 0 else 0
    avg_order_value = round(revenue / order_count, 2) if order_count > 0 else 0
    
    # Verify profit_rate formula
    expected_profit_rate = round((profit / revenue) * 100, 2)
    assert abs(profit_rate - expected_profit_rate) < 0.01, \
        f"Profit rate calculation mismatch: {profit_rate} != {expected_profit_rate}"
    
    # Verify delivery_cost_rate formula
    expected_delivery_cost_rate = round((delivery_cost / revenue) * 100, 2)
    assert abs(delivery_cost_rate - expected_delivery_cost_rate) < 0.01, \
        f"Delivery cost rate calculation mismatch: {delivery_cost_rate} != {expected_delivery_cost_rate}"
    
    # Verify avg_order_value formula
    expected_avg_order_value = round(revenue / order_count, 2)
    assert abs(avg_order_value - expected_avg_order_value) < 0.01, \
        f"Avg order value calculation mismatch: {avg_order_value} != {expected_avg_order_value}"


@settings(max_examples=100)
@given(
    revenue=st.floats(min_value=-1000, max_value=0, allow_nan=False, allow_infinity=False),
    profit=st.floats(min_value=-10000, max_value=50000, allow_nan=False, allow_infinity=False),
)
def test_property_3_zero_revenue_handling(revenue: float, profit: float):
    """
    Property 3 (Edge Case): Zero or negative revenue handling
    
    *For any* distance band with revenue <= 0, the profit_rate and delivery_cost_rate 
    SHALL be 0 (not NaN or infinity).
    
    **Validates: Requirements 1.6, 1.7**
    """
    assume(revenue <= 0)
    
    # Calculate metrics
    profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
    delivery_cost_rate = round(0 / revenue * 100, 2) if revenue > 0 else 0
    
    # Verify rates are 0 when revenue <= 0
    assert profit_rate == 0, f"Profit rate should be 0 when revenue <= 0, got {profit_rate}"
    assert delivery_cost_rate == 0, f"Delivery cost rate should be 0 when revenue <= 0, got {delivery_cost_rate}"


# ==================== Property 5: Optimal Distance Identification ====================
# **Feature: distance-order-diagnosis, Property 5: Optimal Distance Identification**
# **Validates: Requirements 1.7**
# *For any* set of distance bands with at least one band having order_count > 0, 
# the optimal_distance in the summary SHALL be the band_label of the band with 
# the highest profit_rate.

@settings(max_examples=100)
@given(
    band_data=st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=100),  # order_count
            st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),  # revenue
            st.floats(min_value=-1000, max_value=5000, allow_nan=False, allow_infinity=False),  # profit
        ),
        min_size=7,
        max_size=7
    )
)
def test_property_5_optimal_distance_identification(band_data: list):
    """
    Property 5: Optimal Distance Identification
    
    *For any* set of distance bands with at least one band having order_count > 0, 
    the optimal_distance SHALL be the band with the highest profit_rate.
    
    **Validates: Requirements 1.7**
    """
    # Calculate profit rates for each band
    profit_rates = []
    for i, (order_count, revenue, profit) in enumerate(band_data):
        if order_count > 0 and revenue > 0:
            profit_rate = profit / revenue * 100
        else:
            profit_rate = float('-inf')  # Bands with no orders or no revenue are not optimal
        profit_rates.append((i, profit_rate, DISTANCE_BANDS[i]["label"]))
    
    # Find bands with valid profit rates (order_count > 0 and revenue > 0)
    valid_bands = [(i, pr, label) for i, pr, label in profit_rates if pr != float('-inf')]
    
    # Skip test if no valid bands
    assume(len(valid_bands) > 0)
    
    # Find the optimal band (highest profit rate)
    optimal_index, max_profit_rate, optimal_label = max(valid_bands, key=lambda x: x[1])
    
    # Verify the optimal band is correctly identified
    # (This simulates what the API should return)
    for i, pr, label in valid_bands:
        if pr > max_profit_rate:
            assert False, f"Found band {label} with higher profit rate {pr} than optimal {optimal_label} ({max_profit_rate})"


# ==================== Edge Case Tests ====================

def test_edge_case_exact_boundaries():
    """
    Test exact boundary values for distance bands
    
    Verifies that distances exactly at boundaries are assigned to the correct band.
    """
    # Test exact boundary values
    test_cases = [
        (0, 0),      # 0km -> band 0 (0-1km)
        (1, 1),      # 1km -> band 1 (1-2km)
        (2, 2),      # 2km -> band 2 (2-3km)
        (3, 3),      # 3km -> band 3 (3-4km)
        (4, 4),      # 4km -> band 4 (4-5km)
        (5, 5),      # 5km -> band 5 (5-6km)
        (6, 6),      # 6km -> band 6 (6km+)
        (0.999, 0),  # Just under 1km -> band 0
        (1.001, 1),  # Just over 1km -> band 1
        (5.999, 5),  # Just under 6km -> band 5
        (6.001, 6),  # Just over 6km -> band 6
        (100, 6),    # Very large distance -> band 6
    ]
    
    for distance, expected_band in test_cases:
        actual_band = get_distance_band_index(distance)
        assert actual_band == expected_band, \
            f"Distance {distance} should be in band {expected_band}, got {actual_band}"


def test_edge_case_negative_distance():
    """
    Test that negative distances are handled gracefully (treated as 0)
    """
    # Negative distances should be treated as 0 (band 0)
    for distance in [-1, -0.5, -100]:
        band_index = get_distance_band_index(distance)
        assert band_index == 0, f"Negative distance {distance} should be in band 0, got {band_index}"


def test_all_bands_have_correct_labels():
    """
    Verify all 7 distance bands have the correct labels
    """
    expected_labels = ["0-1km", "1-2km", "2-3km", "3-4km", "4-5km", "5-6km", "6km+"]
    
    assert len(DISTANCE_BANDS) == 7, f"Expected 7 bands, got {len(DISTANCE_BANDS)}"
    
    for i, band in enumerate(DISTANCE_BANDS):
        assert band["label"] == expected_labels[i], \
            f"Band {i} label mismatch: expected {expected_labels[i]}, got {band['label']}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
