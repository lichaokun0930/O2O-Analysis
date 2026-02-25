# -*- coding: utf-8 -*-
"""
测试预聚合表 vs 原始查询（现有看板系统逻辑）的差异

目的：验证预聚合表的数据是否与现有看板系统计算逻辑一致
"""

import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent / "backend" / "app"
sys.path.insert(0, str(APP_DIR))

from database.connection import SessionLocal
from sqlalchemy import text
import pandas as pd
import numpy as np


# ==================== 复制现有看板系统的计算逻辑 ====================

PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]


def calculate_order_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """统一的订单指标计算函数（与现有看板系统一致）"""
    if df.empty or '订单ID' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['订单ID'] = df['订单ID'].astype(str)
    
    cost_field = '商品采购成本' if '商品采购成本' in df.columns else '成本'
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
    }
    
    if sales_field in df.columns:
        agg_dict[sales_field] = 'sum'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if cost_field in df.columns:
        agg_dict[cost_field] = 'sum'
    
    for field in ['满减金额', '商品减免金额', '新客减免金额', '渠道', '门店名称', '日期', 
                  '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    if cost_field == '成本' and cost_field in order_agg.columns:
        order_agg['商品采购成本'] = order_agg['成本']
    
    if '平台服务费' not in order_agg.columns:
        order_agg['平台服务费'] = 0
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
    
    if '企客后返' not in order_agg.columns:
        order_agg['企客后返'] = 0
    order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
    
    if '平台佣金' not in order_agg.columns:
        order_agg['平台佣金'] = order_agg['平台服务费']
    order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    
    if '利润额' not in order_agg.columns:
        order_agg['利润额'] = 0
    order_agg['利润额'] = order_agg['利润额'].fillna(0)
    
    # 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    # 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] -
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
        order_agg['企客后返']
    )
    
    # 商家活动成本 = 7个营销字段之和
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = 0
    for field in marketing_fields:
        if field in order_agg.columns:
            order_agg['商家活动成本'] += order_agg[field].fillna(0)
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        order_agg = order_agg[~invalid_orders].copy()
    
    return order_agg


def calculate_gmv(df: pd.DataFrame) -> dict:
    """计算GMV（与现有看板系统一致）"""
    if df.empty:
        return {'gmv': 0, 'marketing_cost': 0, 'marketing_cost_rate': 0}
    
    df = df.copy()
    
    # 剔除商品原价 <= 0 的行
    valid_df = df[df['商品原价'] > 0].copy() if '商品原价' in df.columns else df
    
    # GMV = 商品原价×销量 + 打包袋金额 + 用户支付配送费
    sales_field = '月售' if '月售' in valid_df.columns else '销量'
    
    original_price_sales = (valid_df['商品原价'] * valid_df[sales_field]).sum() if '商品原价' in valid_df.columns else 0
    
    # 打包袋和配送费是订单级字段，需要按订单去重
    if not valid_df.empty:
        order_level = valid_df.groupby('订单ID').agg({
            '打包袋金额': 'first',
            '用户支付配送费': 'first'
        }).reset_index()
        packaging_fee = order_level['打包袋金额'].sum()
        user_delivery_fee = order_level['用户支付配送费'].sum()
    else:
        packaging_fee = 0
        user_delivery_fee = 0
    
    gmv = original_price_sales + packaging_fee + user_delivery_fee
    
    # 营销成本（7字段）- 订单级
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
    if not valid_df.empty:
        order_marketing = valid_df.groupby('订单ID').agg({f: 'first' for f in marketing_fields if f in valid_df.columns}).reset_index()
        marketing_cost = sum(order_marketing[f].sum() for f in marketing_fields if f in order_marketing.columns)
    else:
        marketing_cost = 0
    
    marketing_cost_rate = (marketing_cost / gmv * 100) if gmv > 0 else 0
    
    return {
        'gmv': gmv,
        'marketing_cost': marketing_cost,
        'marketing_cost_rate': marketing_cost_rate
    }


def test_store_comparison(store_name: str, start_date: str, end_date: str):
    """
    对比单个门店的预聚合表数据 vs 原始查询数据
    """
    session = SessionLocal()
    
    print("=" * 80)
    print(f"测试门店: {store_name}")
    print(f"日期范围: {start_date} ~ {end_date}")
    print("=" * 80)
    
    # ==================== 1. 预聚合表查询 ====================
    print("\n【1. 预聚合表数据】")
    sql_agg = f"""
    SELECT 
        SUM(order_count) as order_count,
        SUM(total_revenue) as total_revenue,
        SUM(total_profit) as total_profit,
        SUM(delivery_net_cost) as delivery_net_cost,
        SUM(total_marketing_cost) as total_marketing_cost,
        SUM(COALESCE(gmv, 0)) as gmv
    FROM store_daily_summary
    WHERE store_name = :store_name
      AND summary_date >= :start_date
      AND summary_date <= :end_date
    """
    result_agg = session.execute(text(sql_agg), {
        'store_name': store_name,
        'start_date': start_date,
        'end_date': end_date
    })
    agg_data = result_agg.fetchone()
    
    if agg_data:
        agg_order_count = int(agg_data[0] or 0)
        agg_revenue = float(agg_data[1] or 0)
        agg_profit = float(agg_data[2] or 0)
        agg_delivery = float(agg_data[3] or 0)
        agg_marketing = float(agg_data[4] or 0)
        agg_gmv = float(agg_data[5] or 0)
        
        print(f"  订单数: {agg_order_count}")
        print(f"  销售额: ¥{agg_revenue:,.2f}")
        print(f"  利润: ¥{agg_profit:,.2f}")
        print(f"  配送净成本: ¥{agg_delivery:,.2f}")
        print(f"  营销成本: ¥{agg_marketing:,.2f}")
        print(f"  GMV: ¥{agg_gmv:,.2f}")
        if agg_order_count > 0:
            print(f"  客单价: ¥{agg_revenue/agg_order_count:.2f}")
        if agg_revenue > 0:
            print(f"  利润率: {agg_profit/agg_revenue*100:.2f}%")
        if agg_gmv > 0:
            print(f"  营销成本率: {agg_marketing/agg_gmv*100:.2f}%")
    else:
        print("  无数据")
        agg_order_count = agg_revenue = agg_profit = agg_delivery = agg_marketing = agg_gmv = 0
    
    # ==================== 2. 原始查询（现有看板系统逻辑） ====================
    print("\n【2. 原始查询数据（现有看板系统逻辑）】")
    
    # 从数据库加载原始订单数据
    sql_raw = f"""
    SELECT 
        order_id,
        store_name,
        date,
        channel,
        product_name,
        category_level1,
        category_level3,
        COALESCE(quantity, 1) as quantity,
        COALESCE(actual_price, 0) as actual_price,
        COALESCE(price, 0) as price,
        COALESCE(original_price, 0) as original_price,
        COALESCE(cost, 0) as cost,
        COALESCE(profit, 0) as profit,
        COALESCE(delivery_fee, 0) as delivery_fee,
        COALESCE(platform_service_fee, 0) as platform_service_fee,
        COALESCE(commission, 0) as commission,
        COALESCE(amount, 0) as amount,
        COALESCE(corporate_rebate, 0) as corporate_rebate,
        COALESCE(user_paid_delivery_fee, 0) as user_paid_delivery_fee,
        COALESCE(delivery_discount, 0) as delivery_discount,
        COALESCE(full_reduction, 0) as full_reduction,
        COALESCE(product_discount, 0) as product_discount,
        COALESCE(new_customer_discount, 0) as new_customer_discount,
        COALESCE(merchant_voucher, 0) as merchant_voucher,
        COALESCE(merchant_share, 0) as merchant_share,
        COALESCE(gift_amount, 0) as gift_amount,
        COALESCE(other_merchant_discount, 0) as other_merchant_discount,
        COALESCE(packaging_fee, 0) as packaging_fee
    FROM orders
    WHERE store_name = :store_name
      AND DATE(date) >= :start_date
      AND DATE(date) <= :end_date
    """
    result_raw = session.execute(text(sql_raw), {
        'store_name': store_name,
        'start_date': start_date,
        'end_date': end_date
    })
    
    # 转换为DataFrame
    columns = [
        '订单ID', '门店名称', '日期', '渠道', '商品名称', '一级分类名', '三级分类名',
        '月售', '实收价格', '商品实售价', '商品原价', '商品采购成本', '利润额',
        '物流配送费', '平台服务费', '平台佣金', '预计订单收入', '企客后返',
        '用户支付配送费', '配送费减免金额', '满减金额', '商品减免金额', '新客减免金额',
        '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '打包袋金额'
    ]
    
    rows = result_raw.fetchall()
    df = pd.DataFrame(rows, columns=columns)
    
    if df.empty:
        print("  无数据")
        raw_order_count = raw_revenue = raw_profit = raw_delivery = raw_marketing = raw_gmv = 0
    else:
        # 使用现有看板系统的计算函数
        order_agg = calculate_order_metrics(df)
        gmv_result = calculate_gmv(df)
        
        raw_order_count = len(order_agg)
        raw_revenue = float(order_agg['实收价格'].sum())
        raw_profit = float(order_agg['订单实际利润'].sum())
        raw_delivery = float(order_agg['配送净成本'].sum())
        raw_marketing = float(order_agg['商家活动成本'].sum())
        raw_gmv = gmv_result['gmv']
        
        print(f"  订单数: {raw_order_count}")
        print(f"  销售额: ¥{raw_revenue:,.2f}")
        print(f"  利润: ¥{raw_profit:,.2f}")
        print(f"  配送净成本: ¥{raw_delivery:,.2f}")
        print(f"  营销成本: ¥{raw_marketing:,.2f}")
        print(f"  GMV: ¥{raw_gmv:,.2f}")
        if raw_order_count > 0:
            print(f"  客单价: ¥{raw_revenue/raw_order_count:.2f}")
        if raw_revenue > 0:
            print(f"  利润率: {raw_profit/raw_revenue*100:.2f}%")
        if raw_gmv > 0:
            print(f"  营销成本率: {raw_marketing/raw_gmv*100:.2f}%")
    
    # ==================== 3. 差异对比 ====================
    print("\n【3. 差异对比】")
    
    def compare(name, agg_val, raw_val):
        diff = agg_val - raw_val
        pct = (diff / raw_val * 100) if raw_val != 0 else 0
        status = "✅" if abs(pct) < 1 else "❌"
        print(f"  {status} {name}: 预聚合={agg_val:,.2f}, 原始={raw_val:,.2f}, 差异={diff:,.2f} ({pct:+.1f}%)")
        return abs(pct) < 1
    
    results = []
    results.append(compare("订单数", agg_order_count, raw_order_count))
    results.append(compare("销售额", agg_revenue, raw_revenue))
    results.append(compare("利润", agg_profit, raw_profit))
    results.append(compare("配送净成本", agg_delivery, raw_delivery))
    results.append(compare("营销成本", agg_marketing, raw_marketing))
    results.append(compare("GMV", agg_gmv, raw_gmv))
    
    session.close()
    
    return all(results)


def test_all_stores():
    """测试所有门店"""
    session = SessionLocal()
    
    # 获取所有门店
    result = session.execute(text("SELECT DISTINCT store_name FROM orders"))
    stores = [row[0] for row in result]
    
    # 获取日期范围
    result = session.execute(text("SELECT MIN(DATE(date)), MAX(DATE(date)) FROM orders"))
    date_range = result.fetchone()
    start_date = str(date_range[0])
    end_date = str(date_range[1])
    
    session.close()
    
    print("\n" + "=" * 80)
    print("测试所有门店")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for store in stores:
        try:
            if test_store_comparison(store, start_date, end_date):
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"测试结果: 通过 {passed}/{passed+failed}, 失败 {failed}/{passed+failed}")
    print("=" * 80)


if __name__ == "__main__":
    # 测试单个门店（兴化店，最近7天）
    test_store_comparison("惠宜选-泰州兴化店", "2026-01-16", "2026-01-22")
    
    print("\n\n")
    
    # 测试单个门店（兴化店，全量数据）
    test_store_comparison("惠宜选-泰州兴化店", "2025-12-24", "2026-01-22")
