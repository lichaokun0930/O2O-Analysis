# -*- coding: utf-8 -*-
"""
诊断Vue版本订单数据问题 - 深度分析

问题描述:
- Vue版本显示灵璧县门店订单总数: 5,847笔
- Dash版本显示灵璧县门店订单总数: 2,771笔
- 差异: 约2倍

关键发现:
- 数据库过滤后订单数 = 5,847 (与Vue一致)
- Dash版本显示 = 2,771
- 说明Dash版本可能使用了不同的数据源或有额外过滤

需要检查:
1. Dash版本是否从数据库加载数据
2. Dash版本是否有额外的过滤条件
3. 数据库数据是否与Excel数据一致
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from datetime import datetime, timedelta

# 导入数据库连接
try:
    from database.connection import SessionLocal
    from database.models import Order
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ 无法导入数据库模块: {e}")
    DATABASE_AVAILABLE = False

# 收费渠道列表（与Dash版本一致）
PLATFORM_FEE_CHANNELS = [
    '饿了么',
    '京东到家',
    '美团共橙',
    '美团闪购',
    '抖音',
    '抖音直播',
    '淘鲜达',
    '京东秒送',
    '美团咖啡店',
    '饿了么咖啡店'
]


def diagnose_order_data():
    """诊断订单数据问题 - 深度分析"""
    
    print("=" * 70)
    print("🔍 Vue版本订单数据诊断 - 深度分析")
    print("=" * 70)
    
    if not DATABASE_AVAILABLE:
        print("❌ 数据库不可用，无法诊断")
        return
    
    session = SessionLocal()
    
    try:
        from sqlalchemy import func
        
        # 1. 查询灵璧县门店数据
        print(f"\n📊 灵璧县门店数据分析:")
        
        lingbi_records = session.query(Order).filter(
            Order.store_name.like('%灵璧%')
        ).all()
        
        if not lingbi_records:
            print("   ❌ 未找到灵璧县门店数据")
            return
        
        # 转换为DataFrame
        data = []
        for order in lingbi_records:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '渠道': order.channel,
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '商品名称': order.product_name,
                '日期': order.date,
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '实收价格': float(order.actual_price or 0),
                '月售': order.quantity or 1,
            })
        
        df = pd.DataFrame(data)
        
        print(f"   总记录数(商品行): {len(df):,}")
        print(f"   唯一订单数: {df['订单ID'].nunique():,}")
        
        # 2. 按订单聚合（模拟calculate_order_metrics）
        print(f"\n🔧 模拟calculate_order_metrics聚合:")
        
        # 计算订单总收入
        df['订单总收入'] = df['实收价格'] * df['月售']
        
        order_agg = df.groupby('订单ID').agg({
            '渠道': 'first',
            '平台服务费': 'sum',
            '平台佣金': 'first',
            '利润额': 'sum',
            '物流配送费': 'first',
            '企客后返': 'sum',
            '订单总收入': 'sum',
            '商品名称': 'count',
            '日期': 'first'
        }).reset_index()
        order_agg.columns = ['订单ID', '渠道', '平台服务费', '平台佣金', '利润额', 
                            '物流配送费', '企客后返', '实收价格', '商品数', '日期']
        
        print(f"   聚合后订单数: {len(order_agg):,}")
        
        # 3. 计算订单实际利润
        order_agg['订单实际利润'] = (
            order_agg['利润额'] -
            order_agg['平台服务费'] -
            order_agg['物流配送费'] +
            order_agg['企客后返']
        )
        
        # 4. 应用渠道过滤规则（Vue版本的逻辑）
        print(f"\n🔧 Vue版本过滤逻辑:")
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        
        print(f"   收费渠道订单数: {is_fee_channel.sum():,}")
        print(f"   平台服务费=0的订单数: {is_zero_fee.sum():,}")
        print(f"   收费渠道且服务费=0: {invalid_orders.sum():,}")
        
        filtered_vue = order_agg[~invalid_orders].copy()
        print(f"   Vue过滤后订单数: {len(filtered_vue):,}")
        
        # 5. 检查是否有其他可能的过滤条件
        print(f"\n🔍 检查其他可能的过滤条件:")
        
        # 检查平台佣金>0的条件
        has_commission = order_agg['平台佣金'] > 0
        has_service_fee = order_agg['平台服务费'] > 0
        has_either = has_commission | has_service_fee
        
        print(f"   平台佣金>0的订单数: {has_commission.sum():,}")
        print(f"   平台服务费>0的订单数: {has_service_fee.sum():,}")
        print(f"   佣金>0 OR 服务费>0: {has_either.sum():,}")
        
        # 尝试不同的过滤条件
        print(f"\n🔧 尝试不同的过滤条件:")
        
        # 条件1: 只保留平台服务费>0的订单
        filtered_1 = order_agg[order_agg['平台服务费'] > 0]
        print(f"   条件1 (服务费>0): {len(filtered_1):,} 订单")
        
        # 条件2: 只保留平台佣金>0的订单
        filtered_2 = order_agg[order_agg['平台佣金'] > 0]
        print(f"   条件2 (佣金>0): {len(filtered_2):,} 订单")
        
        # 条件3: 服务费>0 OR 佣金>0
        filtered_3 = order_agg[(order_agg['平台服务费'] > 0) | (order_agg['平台佣金'] > 0)]
        print(f"   条件3 (服务费>0 OR 佣金>0): {len(filtered_3):,} 订单")
        
        # 条件4: 服务费>0 AND 佣金>0
        filtered_4 = order_agg[(order_agg['平台服务费'] > 0) & (order_agg['平台佣金'] > 0)]
        print(f"   条件4 (服务费>0 AND 佣金>0): {len(filtered_4):,} 订单")
        
        # 6. 检查渠道分布
        print(f"\n📊 渠道分布对比:")
        for channel in order_agg['渠道'].unique():
            ch_data = order_agg[order_agg['渠道'] == channel]
            ch_fee_zero = ch_data[ch_data['平台服务费'] <= 0]
            ch_commission_zero = ch_data[ch_data['平台佣金'] <= 0]
            print(f"   {channel}:")
            print(f"      总订单: {len(ch_data):,}")
            print(f"      服务费=0: {len(ch_fee_zero):,}")
            print(f"      佣金=0: {len(ch_commission_zero):,}")
        
        # 7. 对比结果
        print(f"\n" + "=" * 70)
        print(f"📊 对比结果:")
        print(f"   Vue版本显示: 5,847 笔")
        print(f"   Dash版本显示: 2,771 笔")
        print(f"   差异: {5847 - 2771:,} 笔")
        print(f"\n   数据库分析:")
        print(f"   - 原始订单数: {len(order_agg):,}")
        print(f"   - Vue过滤后: {len(filtered_vue):,}")
        print(f"   - 服务费>0: {len(filtered_1):,}")
        print(f"   - 佣金>0: {len(filtered_2):,}")
        print(f"   - 服务费>0 OR 佣金>0: {len(filtered_3):,}")
        
        # 8. 找出最接近2771的条件
        print(f"\n🎯 最接近Dash版本(2,771)的条件:")
        conditions = [
            ("Vue过滤", len(filtered_vue)),
            ("服务费>0", len(filtered_1)),
            ("佣金>0", len(filtered_2)),
            ("服务费>0 OR 佣金>0", len(filtered_3)),
            ("服务费>0 AND 佣金>0", len(filtered_4)),
        ]
        
        for name, count in sorted(conditions, key=lambda x: abs(x[1] - 2771)):
            diff = count - 2771
            print(f"   {name}: {count:,} (差异: {diff:+,})")
        
    finally:
        session.close()


if __name__ == "__main__":
    diagnose_order_data()
