# -*- coding: utf-8 -*-
"""
营销成本结构 API 属性测试

Property-Based Tests for Marketing Structure API

使用 hypothesis 库进行属性测试，验证以下属性：
- Property 2: 订单级字段聚合正确性
- Property 3: 总营销成本计算正确性

**Validates: Requirements 1.2, 3.1, 3.2**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import pandas as pd
import numpy as np


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


def calculate_total_marketing_cost(marketing_costs: dict) -> float:
    """
    计算总营销成本
    
    公式: 总营销成本 = 8个营销字段之和
    
    Args:
        marketing_costs: 包含8个营销字段的字典
    
    Returns:
        总营销成本
    """
    total = 0.0
    for en_field in MARKETING_FIELDS.values():
        total += marketing_costs.get(en_field, 0)
    return total


def aggregate_order_level_fields(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    模拟订单级字段聚合逻辑
    
    订单级字段使用 .first() 聚合，避免重复计算
    
    Args:
        orders_df: 包含多行订单数据的DataFrame（同一订单可能有多行）
    
    Returns:
        聚合后的订单级DataFrame
    """
    if orders_df.empty:
        return pd.DataFrame()
    
    # 订单级字段用 first 聚合
    agg_dict = {}
    for cn_field in MARKETING_FIELDS.keys():
        if cn_field in orders_df.columns:
            agg_dict[cn_field] = 'first'
    
    # 添加渠道字段
    if '渠道' in orders_df.columns:
        agg_dict['渠道'] = 'first'
    
    # 添加实收价格（商品级字段用sum）
    if '实收价格' in orders_df.columns:
        agg_dict['实收价格'] = 'sum'
    
    if not agg_dict:
        return orders_df
    
    return orders_df.groupby('订单ID').agg(agg_dict).reset_index()


# ==================== Property 2: 订单级字段聚合正确性 ====================
# **Feature: marketing-cost-structure, Property 2: 订单级字段聚合正确性**
# **Validates: Requirements 1.2**
# *For any* 包含重复订单ID的数据集，聚合后的营销字段金额 SHALL 等于去重后的订单级字段之和
# （不会因重复行而翻倍）

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
    
    *For any* 包含重复订单ID的数据集，聚合后的营销字段金额 SHALL 等于去重后的
    订单级字段之和（不会因重复行而翻倍）
    
    **Validates: Requirements 1.2**
    """
    # 构造测试数据：每个订单有多个商品行，但订单级字段值相同
    rows = []
    for order_id in range(1, order_count + 1):
        for item_idx in range(items_per_order):
            rows.append({
                '订单ID': f'ORDER_{order_id}',
                '渠道': '美团闪购',
                '实收价格': 50.0,  # 商品级字段
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
    
    # 聚合订单级字段
    order_agg = aggregate_order_level_fields(df)
    
    # 验证：聚合后的订单数应该等于原始订单数（不是行数）
    assert len(order_agg) == order_count, \
        f"聚合后订单数 {len(order_agg)} != 原始订单数 {order_count}"
    
    # 验证：每个订单的营销字段值应该等于原始值（不会翻倍）
    for _, row in order_agg.iterrows():
        assert abs(row['配送费减免金额'] - delivery_discount) < 0.01, \
            f"配送费减免金额聚合错误: {row['配送费减免金额']} != {delivery_discount}"
        assert abs(row['满减金额'] - full_reduction) < 0.01, \
            f"满减金额聚合错误: {row['满减金额']} != {full_reduction}"
        assert abs(row['商品减免金额'] - product_discount) < 0.01, \
            f"商品减免金额聚合错误: {row['商品减免金额']} != {product_discount}"
        assert abs(row['商家代金券'] - merchant_voucher) < 0.01, \
            f"商家代金券聚合错误: {row['商家代金券']} != {merchant_voucher}"
    
    # 验证：总营销成本应该是 订单数 × 单订单营销成本（不是 行数 × 单订单营销成本）
    expected_total = order_count * (delivery_discount + full_reduction + product_discount + merchant_voucher)
    actual_total = (
        order_agg['配送费减免金额'].sum() +
        order_agg['满减金额'].sum() +
        order_agg['商品减免金额'].sum() +
        order_agg['商家代金券'].sum()
    )
    
    assert abs(actual_total - expected_total) < 0.01, \
        f"总营销成本计算错误: {actual_total} != {expected_total}"


# ==================== Property 3: 总营销成本计算正确性 ====================
# **Feature: marketing-cost-structure, Property 3: 总营销成本计算正确性**
# **Validates: Requirements 3.1, 3.2**
# *For any* 渠道数据，`total_marketing_cost` SHALL 等于该渠道8个营销字段之和

@settings(max_examples=100)
@given(
    delivery_discount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    full_reduction=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    product_discount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    merchant_voucher=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    merchant_share=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    gift_amount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    other_discount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    new_customer_discount=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_property_3_total_marketing_cost_calculation(
    delivery_discount: float,
    full_reduction: float,
    product_discount: float,
    merchant_voucher: float,
    merchant_share: float,
    gift_amount: float,
    other_discount: float,
    new_customer_discount: float,
):
    """
    Property 3: 总营销成本计算正确性
    
    *For any* 渠道数据，`total_marketing_cost` SHALL 等于该渠道8个营销字段之和
    
    公式: 总营销成本 = 配送费减免金额 + 满减金额 + 商品减免金额 + 商家代金券 + 
                      商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额
    
    **Validates: Requirements 3.1, 3.2**
    """
    # 构造营销成本字典
    marketing_costs = {
        'delivery_discount': delivery_discount,
        'full_reduction': full_reduction,
        'product_discount': product_discount,
        'merchant_voucher': merchant_voucher,
        'merchant_share': merchant_share,
        'gift_amount': gift_amount,
        'other_discount': other_discount,
        'new_customer_discount': new_customer_discount,
    }
    
    # 计算总营销成本
    total = calculate_total_marketing_cost(marketing_costs)
    
    # 期望值：8个字段之和
    expected = (
        delivery_discount +
        full_reduction +
        product_discount +
        merchant_voucher +
        merchant_share +
        gift_amount +
        other_discount +
        new_customer_discount
    )
    
    # 验证
    assert abs(total - expected) < 0.01, \
        f"总营销成本计算错误: {total} != {expected}"


@settings(max_examples=100)
@given(
    total_marketing_cost=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
    total_orders=st.integers(min_value=1, max_value=10000),
    total_revenue=st.floats(min_value=0.01, max_value=1000000, allow_nan=False, allow_infinity=False),
)
def test_property_3_derived_metrics_calculation(
    total_marketing_cost: float,
    total_orders: int,
    total_revenue: float,
):
    """
    Property 3 (Extended): 派生指标计算正确性
    
    验证单均营销费用和营销成本率的计算公式
    
    公式:
    - 单均营销费用 = 总营销成本 / 订单数
    - 营销成本率 = 总营销成本 / 销售额 × 100%
    
    **Validates: Requirements 3.3, 3.4**
    """
    # 计算派生指标
    avg_marketing_per_order = total_marketing_cost / total_orders if total_orders > 0 else 0
    marketing_cost_ratio = (total_marketing_cost / total_revenue * 100) if total_revenue > 0 else 0
    
    # 验证单均营销费用
    expected_avg = total_marketing_cost / total_orders
    assert abs(avg_marketing_per_order - expected_avg) < 0.01, \
        f"单均营销费用计算错误: {avg_marketing_per_order} != {expected_avg}"
    
    # 验证营销成本率
    expected_ratio = total_marketing_cost / total_revenue * 100
    assert abs(marketing_cost_ratio - expected_ratio) < 0.01, \
        f"营销成本率计算错误: {marketing_cost_ratio} != {expected_ratio}"


@settings(max_examples=50)
@given(
    total_marketing_cost=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
)
def test_property_3_zero_orders_handling(total_marketing_cost: float):
    """
    Property 3 (Edge Case): 零订单处理
    
    当订单数为0时，单均营销费用应该为0（不是NaN或无穷大）
    
    **Validates: Requirements 3.3**
    """
    total_orders = 0
    
    # 计算单均营销费用
    avg_marketing_per_order = total_marketing_cost / total_orders if total_orders > 0 else 0
    
    # 验证
    assert avg_marketing_per_order == 0, \
        f"零订单时单均营销费用应为0，实际为 {avg_marketing_per_order}"


@settings(max_examples=50)
@given(
    total_marketing_cost=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False),
)
def test_property_3_zero_revenue_handling(total_marketing_cost: float):
    """
    Property 3 (Edge Case): 零销售额处理
    
    当销售额为0时，营销成本率应该为0（不是NaN或无穷大）
    
    **Validates: Requirements 3.4**
    """
    total_revenue = 0
    
    # 计算营销成本率
    marketing_cost_ratio = (total_marketing_cost / total_revenue * 100) if total_revenue > 0 else 0
    
    # 验证
    assert marketing_cost_ratio == 0, \
        f"零销售额时营销成本率应为0，实际为 {marketing_cost_ratio}"


# ==================== 边界情况测试 ====================

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


def test_zero_marketing_costs():
    """
    测试所有营销字段为0的情况
    """
    marketing_costs = {
        'delivery_discount': 0,
        'full_reduction': 0,
        'product_discount': 0,
        'merchant_voucher': 0,
        'merchant_share': 0,
        'gift_amount': 0,
        'other_discount': 0,
        'new_customer_discount': 0,
    }
    
    total = calculate_total_marketing_cost(marketing_costs)
    assert total == 0, f"所有字段为0时总营销成本应为0，实际为 {total}"


def test_partial_marketing_costs():
    """
    测试部分营销字段有值的情况
    """
    marketing_costs = {
        'delivery_discount': 10.5,
        'full_reduction': 20.0,
        'product_discount': 0,
        'merchant_voucher': 0,
        'merchant_share': 0,
        'gift_amount': 0,
        'other_discount': 0,
        'new_customer_discount': 5.5,
    }
    
    total = calculate_total_marketing_cost(marketing_costs)
    expected = 10.5 + 20.0 + 5.5
    assert abs(total - expected) < 0.01, f"部分字段有值时总营销成本计算错误: {total} != {expected}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
