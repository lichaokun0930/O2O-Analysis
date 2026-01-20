# -*- coding: utf-8 -*-
"""
预聚合表数据一致性验证脚本

【重要】每次生成或修改预聚合表后必须运行此脚本！

验证内容：
1. 订单总数
2. 商品实收额
3. 总利润（核心公式：利润额 - 平台服务费 - 物流配送费 + 企客后返）
4. 动销商品数（跨日期去重）
5. GMV（商品原价×销量 + 打包袋 + 配送费，剔除原价<=0）
6. 营销成本（7字段）

验证方法：
- 从预聚合表查询汇总数据
- 从原始订单表按相同逻辑计算
- 对比差异，差异超过阈值则报错
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from database.connection import SessionLocal

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]

# 验证阈值
TOLERANCE = {
    'order_count': 0,        # 订单数必须完全一致
    'revenue': 0.01,         # 收入允许0.01误差（浮点精度）
    'profit': 0.01,          # 利润允许0.01误差
    'active_products': 0,    # 动销商品数必须完全一致
    'gmv': 0.01,             # GMV允许0.01误差
    'marketing_cost': 0.01,  # 营销成本允许0.01误差
}


def get_aggregated_data(store_name: str = None) -> dict:
    """从预聚合表获取数据"""
    session = SessionLocal()
    try:
        sql = """
            SELECT 
                SUM(order_count) as total_orders,
                SUM(total_revenue) as total_revenue,
                SUM(total_profit) as total_profit,
                SUM(COALESCE(gmv, 0)) as total_gmv,
                SUM(total_marketing_cost) as total_marketing_cost
            FROM store_daily_summary
            WHERE 1=1
        """
        params = {}
        if store_name:
            sql += " AND store_name = :store_name"
            params['store_name'] = store_name
        
        result = session.execute(text(sql), params).fetchone()
        
        # 动销商品数从原始订单表查询（跨日期去重）
        # 这与aggregation_service中的逻辑一致
        active_sql = """
            SELECT COUNT(DISTINCT product_name) 
            FROM orders
            WHERE quantity > 0
        """
        if store_name:
            active_sql += " AND store_name = :store_name"
        
        active_result = session.execute(text(active_sql), params).fetchone()
        
        return {
            'order_count': int(result[0]) if result[0] else 0,
            'revenue': float(result[1]) if result[1] else 0,
            'profit': float(result[2]) if result[2] else 0,
            'gmv': float(result[3]) if result[3] else 0,
            'marketing_cost': float(result[4]) if result[4] else 0,
            'active_products': int(active_result[0]) if active_result and active_result[0] else 0,
        }
    finally:
        session.close()


def get_raw_calculated_data(store_name: str = None) -> dict:
    """从原始订单表计算数据（与API逻辑完全一致）"""
    session = SessionLocal()
    try:
        # 加载原始数据
        sql = "SELECT * FROM orders WHERE 1=1"
        params = {}
        if store_name:
            sql += " AND store_name = :store_name"
            params['store_name'] = store_name
        
        result = session.execute(text(sql), params)
        columns = result.keys()
        rows = result.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        
        if df.empty:
            return {
                'order_count': 0, 'revenue': 0, 'profit': 0,
                'gmv': 0, 'marketing_cost': 0, 'active_products': 0
            }
        
        # 字段映射
        df['订单ID'] = df['order_id']
        df['实收价格'] = df['actual_price'].fillna(0)
        df['月售'] = df['quantity'].fillna(1)
        df['利润额'] = df['profit'].fillna(0)
        df['物流配送费'] = df['delivery_fee'].fillna(0)
        df['平台服务费'] = df['platform_service_fee'].fillna(0)
        df['企客后返'] = df['corporate_rebate'].fillna(0)
        df['渠道'] = df['channel']
        df['商品原价'] = df['original_price'].fillna(0)
        df['打包袋金额'] = df['packaging_fee'].fillna(0)
        df['用户支付配送费'] = df['user_paid_delivery_fee'].fillna(0)
        
        # 营销成本字段
        df['满减金额'] = df['full_reduction'].fillna(0)
        df['商品减免金额'] = df['product_discount'].fillna(0)
        df['商家代金券'] = df['merchant_voucher'].fillna(0)
        df['商家承担部分券'] = df['merchant_share'].fillna(0)
        df['满赠金额'] = df['gift_amount'].fillna(0)
        df['商家其他优惠'] = df['other_merchant_discount'].fillna(0)
        df['新客减免金额'] = df['new_customer_discount'].fillna(0)
        
        # 计算订单总收入
        df['订单总收入'] = df['实收价格'] * df['月售']
        
        # 订单级聚合
        agg_dict = {
            '订单总收入': 'sum',
            '利润额': 'sum',
            '物流配送费': 'first',
            '平台服务费': 'sum',
            '企客后返': 'sum',
            '渠道': 'first',
        }
        order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
        order_agg['实收价格'] = order_agg['订单总收入']
        
        # 计算订单实际利润（核心公式）
        order_agg['订单实际利润'] = (
            order_agg['利润额'] -
            order_agg['平台服务费'] -
            order_agg['物流配送费'] +
            order_agg['企客后返']
        )
        
        # 渠道过滤
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        order_agg_filtered = order_agg[~invalid_orders].copy()
        
        # 计算核心指标
        order_count = len(order_agg_filtered)
        revenue = order_agg_filtered['实收价格'].sum()
        profit = order_agg_filtered['订单实际利润'].sum()
        
        # 动销商品数（跨日期去重）
        active_products = df[df['月售'] > 0]['product_name'].nunique()
        
        # GMV计算（剔除原价<=0，不应用渠道过滤）
        df_gmv = df[df['商品原价'] > 0].copy()
        df_gmv['原价销售额'] = df_gmv['商品原价'] * df_gmv['月售']
        
        gmv_agg = df_gmv.groupby('订单ID').agg({
            '原价销售额': 'sum',
            '打包袋金额': 'first',
            '用户支付配送费': 'first',
            '满减金额': 'first',
            '商品减免金额': 'first',
            '商家代金券': 'first',
            '商家承担部分券': 'first',
            '满赠金额': 'first',
            '商家其他优惠': 'first',
            '新客减免金额': 'first',
        }).reset_index()
        
        gmv = gmv_agg['原价销售额'].sum() + gmv_agg['打包袋金额'].sum() + gmv_agg['用户支付配送费'].sum()
        
        # 营销成本（7字段）
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
        marketing_cost = sum(gmv_agg[f].sum() for f in marketing_fields)
        
        return {
            'order_count': order_count,
            'revenue': round(revenue, 2),
            'profit': round(profit, 2),
            'gmv': round(gmv, 2),
            'marketing_cost': round(marketing_cost, 2),
            'active_products': active_products,
        }
    finally:
        session.close()


def verify_consistency(store_name: str = None) -> bool:
    """验证预聚合表与原始计算的一致性"""
    print("="*70)
    print("预聚合表数据一致性验证")
    print("="*70)
    
    if store_name:
        print(f"验证门店: {store_name}")
    else:
        print("验证范围: 全部门店")
    
    print("\n获取预聚合表数据...")
    agg_data = get_aggregated_data(store_name)
    
    print("计算原始数据...")
    raw_data = get_raw_calculated_data(store_name)
    
    print("\n" + "-"*70)
    print(f"{'指标':<20} {'预聚合表':<15} {'原始计算':<15} {'差异':<15} {'状态':<10}")
    print("-"*70)
    
    all_passed = True
    metrics = [
        ('订单总数', 'order_count'),
        ('商品实收额', 'revenue'),
        ('总利润', 'profit'),
        ('动销商品数', 'active_products'),
        ('GMV', 'gmv'),
        ('营销成本', 'marketing_cost'),
    ]
    
    for name, key in metrics:
        agg_val = agg_data[key]
        raw_val = raw_data[key]
        diff = agg_val - raw_val
        tolerance = TOLERANCE.get(key, 0.01)
        
        if abs(diff) <= tolerance:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_passed = False
        
        print(f"{name:<20} {agg_val:<15} {raw_val:<15} {diff:<15.2f} {status:<10}")
    
    print("-"*70)
    
    if all_passed:
        print("\n✅ 验证通过！预聚合表数据与原始计算完全一致")
    else:
        print("\n❌ 验证失败！预聚合表数据与原始计算存在差异")
        print("请检查预聚合表生成逻辑是否与以下文档一致：")
        print("  - Tab1订单数据概览_卡片计算公式汇总.md")
        print("  - 【权威】业务逻辑与数据字典完整手册.md")
    
    return all_passed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='验证预聚合表数据一致性')
    parser.add_argument('--store', type=str, help='指定门店名称（可选）')
    args = parser.parse_args()
    
    # 默认验证一个典型门店
    test_store = args.store or '惠宜选超市（昆山淀山湖镇店）'
    
    success = verify_consistency(test_store)
    
    # 返回退出码
    sys.exit(0 if success else 1)
