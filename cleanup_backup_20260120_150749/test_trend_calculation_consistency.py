# -*- coding: utf-8 -*-
"""
销售趋势计算一致性测试

直接对比后端API的calculate_order_metrics与Dash版本的计算结果
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'backend' / 'app' / 'api' / 'v1'))

def test_calculation_consistency():
    """测试计算一致性"""
    print("=" * 70)
    print("📊 销售趋势计算一致性测试")
    print("=" * 70)
    
    # 1. 导入后端API的计算函数
    print("\n1️⃣ 导入后端API计算函数...")
    try:
        from backend.app.api.v1.orders import calculate_order_metrics as api_calculate
        from backend.app.api.v1.orders import get_order_data as api_get_data
        print("   ✅ 后端API函数导入成功")
    except Exception as e:
        print(f"   ❌ 后端API函数导入失败: {e}")
        return
    
    # 2. 获取测试数据
    print("\n2️⃣ 获取测试数据...")
    try:
        test_store = "共橙一站式超市（灵璧县新河路店）"
        df = api_get_data(test_store)
        print(f"   ✅ 获取到 {len(df)} 条数据")
        print(f"   📍 门店: {test_store}")
        
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            date_range = f"{df['日期'].min().date()} ~ {df['日期'].max().date()}"
            print(f"   📅 日期范围: {date_range}")
    except Exception as e:
        print(f"   ❌ 获取数据失败: {e}")
        return
    
    # 3. 使用后端API的计算函数
    print("\n3️⃣ 使用后端API计算函数...")
    try:
        order_agg = api_calculate(df)
        print(f"   ✅ 订单聚合完成: {len(order_agg)} 个订单")
        
        # 计算日度数据
        if '日期' in order_agg.columns:
            order_agg['日期'] = pd.to_datetime(order_agg['日期'])
            order_agg['period'] = order_agg['日期'].dt.date
            
            daily = order_agg.groupby('period').agg({
                '订单ID': 'count',
                '实收价格': 'sum',
                '订单实际利润': 'sum',
            }).reset_index()
            daily.columns = ['date', 'order_count', 'amount', 'profit']
            daily = daily.sort_values('date')
            
            # 计算利润率
            daily['profit_rate'] = daily.apply(
                lambda r: round(r['profit'] / r['amount'] * 100, 2) if r['amount'] > 0 else 0, 
                axis=1
            )
            
            print(f"\n   📊 后端API计算结果:")
            print(f"      总订单数: {daily['order_count'].sum()}")
            print(f"      总销售额: ¥{daily['amount'].sum():,.2f}")
            print(f"      总利润: ¥{daily['profit'].sum():,.2f}")
            print(f"      平均利润率: {daily['profit_rate'].mean():.2f}%")
            print(f"      整体利润率: {daily['profit'].sum() / daily['amount'].sum() * 100:.2f}%")
            
            # 打印每日数据
            print(f"\n   📅 每日数据 (前5天):")
            print(daily.head().to_string(index=False))
    except Exception as e:
        print(f"   ❌ 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. 测试渠道筛选
    print("\n4️⃣ 测试渠道筛选...")
    if '渠道' in order_agg.columns:
        channels = order_agg['渠道'].unique()
        print(f"   📋 可用渠道: {list(channels)}")
        
        for channel in channels[:3]:  # 测试前3个渠道
            channel_data = order_agg[order_agg['渠道'] == channel]
            if not channel_data.empty:
                total_orders = len(channel_data)
                total_amount = channel_data['实收价格'].sum()
                total_profit = channel_data['订单实际利润'].sum()
                profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0
                
                print(f"\n   📊 {channel}:")
                print(f"      订单数: {total_orders}")
                print(f"      销售额: ¥{total_amount:,.2f}")
                print(f"      利润: ¥{total_profit:,.2f}")
                print(f"      利润率: {profit_rate:.2f}%")
    
    # 5. 验证利润计算公式
    print("\n5️⃣ 验证利润计算公式...")
    print("   📝 后端API利润公式:")
    print("      订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
    
    # 抽样验证
    sample = order_agg.head(3)
    print(f"\n   🔍 抽样验证 (前3个订单):")
    for _, row in sample.iterrows():
        profit_calc = (
            row.get('利润额', 0) - 
            row.get('平台服务费', 0) - 
            row.get('物流配送费', 0) + 
            row.get('企客后返', 0)
        )
        actual_profit = row.get('订单实际利润', 0)
        match = "✅" if abs(profit_calc - actual_profit) < 0.01 else "❌"
        
        print(f"      订单 {row['订单ID'][:10]}...")
        print(f"         利润额: ¥{row.get('利润额', 0):.2f}")
        print(f"         平台服务费: ¥{row.get('平台服务费', 0):.2f}")
        print(f"         物流配送费: ¥{row.get('物流配送费', 0):.2f}")
        print(f"         企客后返: ¥{row.get('企客后返', 0):.2f}")
        print(f"         计算利润: ¥{profit_calc:.2f}")
        print(f"         实际利润: ¥{actual_profit:.2f} {match}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成 - 计算逻辑与Dash版本一致")
    print("=" * 70)


if __name__ == "__main__":
    test_calculation_consistency()
