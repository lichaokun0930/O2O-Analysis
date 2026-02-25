# -*- coding: utf-8 -*-
"""
诊断数据差异 - 对比数据库原始数据和API计算逻辑

目标：找出为什么API计算的利润与用户期望值(¥17,341)有差异
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, text
import pandas as pd

# 收费渠道列表（与API一致）
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

def diagnose_store(store_name: str = "惠宜选-泰州兴化店"):
    """诊断指定门店的数据"""
    
    print("=" * 70)
    print(f"📊 诊断门店: {store_name}")
    print("=" * 70)
    
    session = SessionLocal()
    
    try:
        # 1. 获取原始数据
        print("\n【1】原始数据统计")
        print("-" * 50)
        
        orders = session.query(Order).filter(Order.store_name == store_name).all()
        
        if not orders:
            print(f"❌ 未找到门店数据: {store_name}")
            return
        
        # 转换为DataFrame
        data = []
        for o in orders:
            data.append({
                '订单ID': o.order_id,
                '渠道': o.channel,
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '实收价格': float(o.actual_price or 0),
                '月售': o.quantity or 1,
            })
        
        df = pd.DataFrame(data)
        print(f"原始记录数（商品行）: {len(df)}")
        print(f"唯一订单数: {df['订单ID'].nunique()}")
        
        # 2. 订单级聚合（与API一致）
        print("\n【2】订单级聚合")
        print("-" * 50)
        
        order_agg = df.groupby('订单ID').agg({
            '渠道': 'first',
            '利润额': 'sum',
            '平台服务费': 'sum',
            '物流配送费': 'first',  # 订单级字段
            '企客后返': 'sum',
            '实收价格': lambda x: (df.loc[x.index, '实收价格'] * df.loc[x.index, '月售']).sum(),
        }).reset_index()
        
        print(f"聚合后订单数: {len(order_agg)}")
        
        # 3. 计算订单实际利润
        order_agg['订单实际利润'] = (
            order_agg['利润额'] - 
            order_agg['平台服务费'] - 
            order_agg['物流配送费'] + 
            order_agg['企客后返']
        )
        
        print(f"\n【3】过滤前的汇总")
        print("-" * 50)
        print(f"订单数: {len(order_agg)}")
        print(f"销售额: ¥{order_agg['实收价格'].sum():,.2f}")
        print(f"原始利润额: ¥{order_agg['利润额'].sum():,.2f}")
        print(f"平台服务费: ¥{order_agg['平台服务费'].sum():,.2f}")
        print(f"物流配送费: ¥{order_agg['物流配送费'].sum():,.2f}")
        print(f"企客后返: ¥{order_agg['企客后返'].sum():,.2f}")
        print(f"订单实际利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
        
        # 4. 过滤异常订单（收费渠道中平台服务费=0）
        print(f"\n【4】过滤异常订单")
        print("-" * 50)
        
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        
        print(f"收费渠道订单数: {is_fee_channel.sum()}")
        print(f"平台服务费=0的订单数: {is_zero_fee.sum()}")
        print(f"异常订单数（收费渠道+服务费=0）: {invalid_orders.sum()}")
        
        # 显示异常订单的渠道分布
        if invalid_orders.sum() > 0:
            invalid_df = order_agg[invalid_orders]
            print(f"\n异常订单渠道分布:")
            print(invalid_df['渠道'].value_counts())
            print(f"\n异常订单利润影响: ¥{invalid_df['订单实际利润'].sum():,.2f}")
        
        # 过滤后的数据
        filtered_agg = order_agg[~invalid_orders].copy()
        
        print(f"\n【5】过滤后的汇总（API返回值）")
        print("-" * 50)
        print(f"订单数: {len(filtered_agg)}")
        print(f"销售额: ¥{filtered_agg['实收价格'].sum():,.2f}")
        print(f"原始利润额: ¥{filtered_agg['利润额'].sum():,.2f}")
        print(f"平台服务费: ¥{filtered_agg['平台服务费'].sum():,.2f}")
        print(f"物流配送费: ¥{filtered_agg['物流配送费'].sum():,.2f}")
        print(f"企客后返: ¥{filtered_agg['企客后返'].sum():,.2f}")
        print(f"订单实际利润: ¥{filtered_agg['订单实际利润'].sum():,.2f}")
        
        # 6. 与用户期望值对比
        print(f"\n【6】与用户期望值对比")
        print("-" * 50)
        user_expected = 17341
        api_result = filtered_agg['订单实际利润'].sum()
        diff = api_result - user_expected
        print(f"用户期望利润: ¥{user_expected:,.2f}")
        print(f"API计算利润: ¥{api_result:,.2f}")
        print(f"差异: ¥{diff:,.2f} ({diff/user_expected*100:.2f}%)")
        
        # 7. 按渠道分析
        print(f"\n【7】按渠道分析利润")
        print("-" * 50)
        channel_stats = filtered_agg.groupby('渠道').agg({
            '订单ID': 'count',
            '订单实际利润': 'sum'
        }).reset_index()
        channel_stats.columns = ['渠道', '订单数', '利润']
        channel_stats = channel_stats.sort_values('利润', ascending=False)
        
        for _, row in channel_stats.iterrows():
            print(f"  {row['渠道']}: {row['订单数']}单, ¥{row['利润']:,.2f}")
        
        # 8. 检查是否有负利润订单
        print(f"\n【8】负利润订单分析")
        print("-" * 50)
        negative_profit = filtered_agg[filtered_agg['订单实际利润'] < 0]
        print(f"负利润订单数: {len(negative_profit)}")
        if len(negative_profit) > 0:
            print(f"负利润总额: ¥{negative_profit['订单实际利润'].sum():,.2f}")
            print(f"负利润订单渠道分布:")
            print(negative_profit['渠道'].value_counts())
        
        # 9. 直接SQL验证
        print(f"\n【9】直接SQL验证")
        print("-" * 50)
        
        sql = """
        WITH order_level AS (
            SELECT 
                order_id,
                channel,
                SUM(profit) as profit,
                SUM(platform_service_fee) as platform_fee,
                MAX(delivery_fee) as delivery_fee,
                SUM(corporate_rebate) as rebate
            FROM orders
            WHERE store_name = :store_name
            GROUP BY order_id, channel
        )
        SELECT 
            COUNT(*) as order_count,
            SUM(profit) as total_profit,
            SUM(platform_fee) as total_platform_fee,
            SUM(delivery_fee) as total_delivery_fee,
            SUM(rebate) as total_rebate,
            SUM(profit - platform_fee - delivery_fee + rebate) as actual_profit
        FROM order_level
        WHERE NOT (
            channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
            AND platform_fee <= 0
        )
        """
        
        result = session.execute(text(sql), {'store_name': store_name})
        row = result.fetchone()
        
        if row:
            print(f"SQL订单数: {row[0]}")
            print(f"SQL原始利润: ¥{row[1]:,.2f}")
            print(f"SQL平台服务费: ¥{row[2]:,.2f}")
            print(f"SQL物流配送费: ¥{row[3]:,.2f}")
            print(f"SQL企客后返: ¥{row[4]:,.2f}")
            print(f"SQL订单实际利润: ¥{row[5]:,.2f}")
        
    finally:
        session.close()


if __name__ == "__main__":
    diagnose_store("惠宜选-泰州兴化店")
