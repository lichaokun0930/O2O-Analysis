# -*- coding: utf-8 -*-
"""
营销成本趋势 API 属性测试

Property-Based Tests for Marketing Trend API

使用 hypothesis 库进行属性测试，验证以下属性：
- Property 2: 订单级字段聚合正确性
- Property 3: 日期过滤正确性

**Validates: Requirements 1.2, 1.4**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import numpy as np
from datetime import date, timedelta


# ==================== 8个营销字段定义（与 orders.py 保持一致） ====================
MARKETING_FIELDS = {
    '配送费减免金额': 'delivery_discount',
    '满减金额': 'full_reduction',
    '商品减免金额': 'product_discount',
    '商家代金券': 'merchant_voucher',
    '商家承担部分券': 'merchant_share',
    '满赠金额': 'gift_amount',
    '商家其他优惠': 'other_discount',
    '新客减免金额': 'new_customer_discount'
}


def aggregate_order_level_fields_by_date(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    模拟按日期聚合订单级字段的逻辑
    
    1. 先按订单ID聚合（订单级字段用first）
    2. 再按日期聚合（sum）
    
    Args:
        orders_df: 包含多行订单数据的DataFrame（同一订单可能有多行）
    
    Returns:
        按日期聚合后的DataFrame
    """
    if orders_df.empty:
        return pd.DataFrame()
    
    # Step 1: 订单级聚合（订单级字段用 first）
    order_agg_dict = {}
    for cn_field in MARKETING_FIELDS.keys():
        if cn_field in orders_df.columns:
            order_agg_dict[cn_field] = 'first'
    
    if '日期' in orders_df.columns:
        order_agg_dict['日期'] = 'first'
    
    if not order_agg_dict:
        return orders_df
    
    order_agg = orders_df.groupby('订单ID').agg(order_agg_dict).reset_index()
    
    # Step 2: 按日期聚合（sum）
    date_agg_dict = {}
    for cn_field in MARKETING_FIELDS.keys():
        if cn_field in order_agg.columns:
            date_agg_dict[cn_field] = 'sum'
    
    if not date_agg_dict:
        return order_agg
    
    # 确保日期是字符串格式
    order_agg['日期_str'] = pd.to_datetime(order_agg['日期']).dt.strftime('%Y-%m-%d')
    
    daily_stats = order_agg.groupby('日期_str').agg(date_agg_dict).reset_index()
    
    return daily_stats


def filter_by_date_range(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """
    按日期范围过滤数据
    
    Args:
        df: 包含日期列的DataFrame
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        过滤后的DataFrame
    """
    if df.empty or '日期' not in df.columns:
        return df
    
    df = df.copy()
    df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
    df = df.dropna(subset=['日期'])
    
    if start_date:
        df = df[df['日期'].dt.date >= start_date]
    if end_date:
        df = df[df['日期'].dt.date <= end_date]
    
    return df


# ==================== Property 2: 订单级字段聚合正确性 ====================
# **Feature: marketing-cost-trend, Property 2: 订单级字段聚合正确性**
# **Validates: Requirements 1.2**
# *For any* 包含重复订单ID的数据集，按日期聚合后的营销字段金额 SHALL 等于
# 去重后的订单级字段之和（不会因重复行而翻倍）

@settings(max_examples=100)
@given(
    order_count=st.integers(min_value=1, max_value=10),
    items_per_order=st.integers(min_value=1, max_value=5),
    delivery_discount=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    full_reduction=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    product_discount=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
    merchant_voucher=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
)
def test_property_2_order_level_aggregation_correctness(
    order_count: int,
    items_per_order: int,
    delivery_discount: float,
    full_reduction: float,
    product_discount: float,
    merchant_voucher: float,
):
    """
    Property 2: 订单级字段聚合正确性
    
    *For any* 包含重复订单ID的数据集，按日期聚合后的营销字段金额 SHALL 等于
    去重后的订单级字段之和（不会因重复行而翻倍）
    
    **Validates: Requirements 1.2**
    """
    # 构造测试数据：每个订单有多个商品行，但订单级字段值相同
    # 所有订单在同一天
    test_date = '2024-01-15'
    rows = []
    for order_id in range(1, order_count + 1):
        for item_idx in range(items_per_order):
            rows.append({
                '订单ID': f'ORDER_{order_id}',
                '日期': test_date,
                '配送费减免金额': delivery_discount,  # 订单级字段
                '满减金额': full_reduction,
                '商品减免金额': product_discount,
                '商家代金券': merchant_voucher,
                '商家承担部分券': 0,
                '满赠金额': 0,
                '商家其他优惠': 0,
                '新客减免金额': 0,
            })
    
    df = pd.DataFrame(rows)
    
    # 按日期聚合
    daily_stats = aggregate_order_level_fields_by_date(df)
    
    # 验证：应该只有一天的数据
    assert len(daily_stats) == 1, \
        f"应该只有1天的数据，实际有 {len(daily_stats)} 天"
    
    # 验证：总营销成本应该是 订单数 × 单订单营销成本（不是 行数 × 单订单营销成本）
    expected_delivery = order_count * delivery_discount
    expected_full_reduction = order_count * full_reduction
    expected_product_discount = order_count * product_discount
    expected_merchant_voucher = order_count * merchant_voucher
    
    actual_delivery = daily_stats['配送费减免金额'].sum()
    actual_full_reduction = daily_stats['满减金额'].sum()
    actual_product_discount = daily_stats['商品减免金额'].sum()
    actual_merchant_voucher = daily_stats['商家代金券'].sum()
    
    assert abs(actual_delivery - expected_delivery) < 0.01, \
        f"配送费减免金额聚合错误: {actual_delivery} != {expected_delivery}"
    assert abs(actual_full_reduction - expected_full_reduction) < 0.01, \
        f"满减金额聚合错误: {actual_full_reduction} != {expected_full_reduction}"
    assert abs(actual_product_discount - expected_product_discount) < 0.01, \
        f"商品减免金额聚合错误: {actual_product_discount} != {expected_product_discount}"
    assert abs(actual_merchant_voucher - expected_merchant_voucher) < 0.01, \
        f"商家代金券聚合错误: {actual_merchant_voucher} != {expected_merchant_voucher}"


@settings(max_examples=100)
@given(
    days=st.integers(min_value=1, max_value=7),
    orders_per_day=st.integers(min_value=1, max_value=5),
    items_per_order=st.integers(min_value=1, max_value=3),
    delivery_discount=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
)
def test_property_2_multi_day_aggregation(
    days: int,
    orders_per_day: int,
    items_per_order: int,
    delivery_discount: float,
):
    """
    Property 2 (Extended): 多日数据聚合正确性
    
    验证多天数据的聚合逻辑
    
    **Validates: Requirements 1.2**
    """
    base_date = date(2024, 1, 1)
    rows = []
    
    for day_offset in range(days):
        current_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        for order_idx in range(orders_per_day):
            order_id = f'ORDER_D{day_offset}_O{order_idx}'
            for item_idx in range(items_per_order):
                rows.append({
                    '订单ID': order_id,
                    '日期': current_date,
                    '配送费减免金额': delivery_discount,
                    '满减金额': 0,
                    '商品减免金额': 0,
                    '商家代金券': 0,
                    '商家承担部分券': 0,
                    '满赠金额': 0,
                    '商家其他优惠': 0,
                    '新客减免金额': 0,
                })
    
    df = pd.DataFrame(rows)
    
    # 按日期聚合
    daily_stats = aggregate_order_level_fields_by_date(df)
    
    # 验证：应该有 days 天的数据
    assert len(daily_stats) == days, \
        f"应该有 {days} 天的数据，实际有 {len(daily_stats)} 天"
    
    # 验证：每天的配送费减免金额应该是 orders_per_day × delivery_discount
    expected_daily_total = orders_per_day * delivery_discount
    
    for _, row in daily_stats.iterrows():
        actual = row['配送费减免金额']
        assert abs(actual - expected_daily_total) < 0.01, \
            f"每日配送费减免金额聚合错误: {actual} != {expected_daily_total}"


# ==================== Property 3: 日期过滤正确性 ====================
# **Feature: marketing-cost-trend, Property 3: 日期过滤正确性**
# **Validates: Requirements 1.4**
# *For any* 指定日期范围的请求，返回的dates数组 SHALL 只包含该日期范围内的日期

@settings(max_examples=100)
@given(
    total_days=st.integers(min_value=5, max_value=30),
    filter_start_offset=st.integers(min_value=0, max_value=10),
    filter_days=st.integers(min_value=1, max_value=10),
)
def test_property_3_date_filter_correctness(
    total_days: int,
    filter_start_offset: int,
    filter_days: int,
):
    """
    Property 3: 日期过滤正确性
    
    *For any* 指定日期范围的请求，返回的dates数组 SHALL 只包含该日期范围内的日期
    
    **Validates: Requirements 1.4**
    """
    # 确保过滤范围在数据范围内
    assume(filter_start_offset + filter_days <= total_days)
    
    base_date = date(2024, 1, 1)
    rows = []
    
    # 生成 total_days 天的数据
    for day_offset in range(total_days):
        current_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        rows.append({
            '订单ID': f'ORDER_{day_offset}',
            '日期': current_date,
            '配送费减免金额': 10.0,
            '满减金额': 5.0,
            '商品减免金额': 0,
            '商家代金券': 0,
            '商家承担部分券': 0,
            '满赠金额': 0,
            '商家其他优惠': 0,
            '新客减免金额': 0,
        })
    
    df = pd.DataFrame(rows)
    
    # 计算过滤日期范围
    filter_start = base_date + timedelta(days=filter_start_offset)
    filter_end = base_date + timedelta(days=filter_start_offset + filter_days - 1)
    
    # 过滤数据
    filtered_df = filter_by_date_range(df, filter_start, filter_end)
    
    # 验证：过滤后的数据应该只包含指定日期范围内的日期
    assert len(filtered_df) == filter_days, \
        f"过滤后应有 {filter_days} 条数据，实际有 {len(filtered_df)} 条"
    
    # 验证：所有日期都在指定范围内
    for _, row in filtered_df.iterrows():
        row_date = pd.to_datetime(row['日期']).date()
        assert filter_start <= row_date <= filter_end, \
            f"日期 {row_date} 不在范围 [{filter_start}, {filter_end}] 内"


@settings(max_examples=50)
@given(
    total_days=st.integers(min_value=5, max_value=20),
)
def test_property_3_no_filter_returns_all(total_days: int):
    """
    Property 3 (Edge Case): 不指定日期范围时返回所有数据
    
    **Validates: Requirements 1.4**
    """
    base_date = date(2024, 1, 1)
    rows = []
    
    for day_offset in range(total_days):
        current_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        rows.append({
            '订单ID': f'ORDER_{day_offset}',
            '日期': current_date,
            '配送费减免金额': 10.0,
            '满减金额': 0,
            '商品减免金额': 0,
            '商家代金券': 0,
            '商家承担部分券': 0,
            '满赠金额': 0,
            '商家其他优惠': 0,
            '新客减免金额': 0,
        })
    
    df = pd.DataFrame(rows)
    
    # 不指定日期范围
    filtered_df = filter_by_date_range(df, None, None)
    
    # 验证：应该返回所有数据
    assert len(filtered_df) == total_days, \
        f"不指定日期范围时应返回所有 {total_days} 条数据，实际返回 {len(filtered_df)} 条"


@settings(max_examples=50)
@given(
    total_days=st.integers(min_value=5, max_value=20),
    filter_start_offset=st.integers(min_value=0, max_value=10),
)
def test_property_3_only_start_date_filter(total_days: int, filter_start_offset: int):
    """
    Property 3 (Edge Case): 只指定开始日期时的过滤
    
    **Validates: Requirements 1.4**
    """
    assume(filter_start_offset < total_days)
    
    base_date = date(2024, 1, 1)
    rows = []
    
    for day_offset in range(total_days):
        current_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
        rows.append({
            '订单ID': f'ORDER_{day_offset}',
            '日期': current_date,
            '配送费减免金额': 10.0,
            '满减金额': 0,
            '商品减免金额': 0,
            '商家代金券': 0,
            '商家承担部分券': 0,
            '满赠金额': 0,
            '商家其他优惠': 0,
            '新客减免金额': 0,
        })
    
    df = pd.DataFrame(rows)
    
    filter_start = base_date + timedelta(days=filter_start_offset)
    
    # 只指定开始日期
    filtered_df = filter_by_date_range(df, filter_start, None)
    
    # 验证：应该返回从开始日期到最后的所有数据
    expected_count = total_days - filter_start_offset
    assert len(filtered_df) == expected_count, \
        f"只指定开始日期时应返回 {expected_count} 条数据，实际返回 {len(filtered_df)} 条"


# ==================== 边界情况测试 ====================

def test_empty_dataframe():
    """
    测试空DataFrame的处理
    """
    df = pd.DataFrame()
    result = aggregate_order_level_fields_by_date(df)
    assert result.empty, "空DataFrame应返回空结果"


def test_single_order_single_day():
    """
    测试单订单单日的情况
    """
    df = pd.DataFrame([{
        '订单ID': 'ORDER_1',
        '日期': '2024-01-15',
        '配送费减免金额': 10.5,
        '满减金额': 20.0,
        '商品减免金额': 5.0,
        '商家代金券': 0,
        '商家承担部分券': 0,
        '满赠金额': 0,
        '商家其他优惠': 0,
        '新客减免金额': 0,
    }])
    
    result = aggregate_order_level_fields_by_date(df)
    
    assert len(result) == 1, "单订单单日应返回1条记录"
    assert abs(result['配送费减免金额'].iloc[0] - 10.5) < 0.01
    assert abs(result['满减金额'].iloc[0] - 20.0) < 0.01
    assert abs(result['商品减免金额'].iloc[0] - 5.0) < 0.01


def test_all_marketing_fields_present():
    """
    验证所有8个营销字段都被正确定义
    """
    expected_fields = [
        'delivery_discount',
        'full_reduction',
        'product_discount',
        'merchant_voucher',
        'merchant_share',
        'gift_amount',
        'other_discount',
        'new_customer_discount'
    ]
    
    assert len(MARKETING_FIELDS) == 8, f"应有8个营销字段，实际有 {len(MARKETING_FIELDS)} 个"
    
    for en_field in expected_fields:
        assert en_field in MARKETING_FIELDS.values(), \
            f"缺少营销字段: {en_field}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
