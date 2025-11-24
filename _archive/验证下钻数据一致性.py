"""
验证下钻分析的数据一致性
对比主看板Tab1渠道卡片和下钻详情页的指标是否一致
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))

def test_data_consistency():
    """测试数据一致性"""
    
    print("="*80)
    print("🔍 下钻数据一致性验证")
    print("="*80)
    
    # 1. 导入主看板模块
    try:
        from 智能门店看板_Dash版 import (
            calculate_order_metrics,
            PLATFORM_FEE_CHANNELS,
            CHANNELS_TO_REMOVE
        )
        print("✅ 成功导入主看板模块")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 2. 加载测试数据
    print("\n📂 加载测试数据...")
    
    # 尝试从默认路径加载
    data_paths = [
        Path("订单数据_2024-11-01至2024-11-07.xlsx"),
        Path("订单数据.xlsx"),
        Path("../订单数据.xlsx"),
    ]
    
    df = None
    for data_path in data_paths:
        if data_path.exists():
            print(f"   找到数据文件: {data_path}")
            try:
                df = pd.read_excel(data_path)
                print(f"   ✅ 成功加载数据: {len(df):,} 行")
                break
            except Exception as e:
                print(f"   ❌ 加载失败: {e}")
                continue
    
    if df is None or df.empty:
        print("⚠️ 未找到测试数据文件,请确保工作目录下有订单数据文件")
        print("   提示: 你也可以启动看板后,GLOBAL_DATA会自动加载")
        return
    print(f"\n📊 数据概况:")
    print(f"   总行数: {len(df):,}")
    print(f"   订单数: {df['订单ID'].nunique():,}")
    
    if '日期' in df.columns:
        print(f"   日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
    
    if '渠道' not in df.columns:
        print("❌ 数据中缺少'渠道'字段")
        return
    
    # 3. 模拟主看板Tab1的计算逻辑
    print(f"\n{'='*80}")
    print("📊 主看板Tab1计算逻辑 (模拟)")
    print("="*80)
    
    # 3.1 订单聚合(与Tab1完全一致)
    order_agg = calculate_order_metrics(df, calc_mode='all_no_fallback')
    print(f"✅ 订单聚合完成: {len(order_agg):,} 订单")
    
    # 3.2 过滤渠道(与_create_channel_comparison_cards一致)
    excluded_channels = ['收银机订单', '闪购小程序'] + CHANNELS_TO_REMOVE
    print(f"\n🚫 排除渠道: {excluded_channels}")
    
    # 确保order_agg有渠道字段
    if '渠道' not in order_agg.columns:
        order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
        order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
    
    order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()
    print(f"✅ 过滤后订单数: {len(order_agg_filtered):,}")
    
    # 3.3 按渠道聚合
    channel_stats = order_agg_filtered.groupby('渠道').agg({
        '订单ID': 'count',
        '实收价格': 'sum' if '实收价格' in order_agg_filtered.columns else lambda x: 0,
        '订单实际利润': 'sum'
    }).reset_index()
    
    channel_stats.columns = ['渠道', '订单数', '销售额', '利润额']
    channel_stats['利润率'] = (channel_stats['利润额'] / channel_stats['销售额'] * 100).fillna(0).round(2)
    
    print(f"\n📈 主看板渠道统计:")
    print(channel_stats.to_string(index=False))
    
    # 4. 模拟下钻页面的计算逻辑
    print(f"\n{'='*80}")
    print("🔍 下钻详情页计算逻辑 (模拟)")
    print("="*80)
    
    drill_down_results = []
    
    for channel_name in channel_stats['渠道'].unique():
        print(f"\n--- {channel_name} ---")
        
        # 4.1 筛选该渠道数据(与render_channel_detail一致)
        channel_data = df[df['渠道'] == channel_name].copy()
        print(f"   原始数据行数: {len(channel_data):,}")
        
        # 4.2 调用calculate_order_metrics(与下钻页面一致)
        channel_order_agg = calculate_order_metrics(channel_data, calc_mode='all_no_fallback')
        print(f"   聚合后订单数: {len(channel_order_agg):,}")
        
        if channel_order_agg.empty:
            print(f"   ⚠️ 聚合后无数据")
            continue
        
        # 4.3 计算指标
        total_orders = len(channel_order_agg)
        
        if '实收价格' in channel_order_agg.columns:
            total_sales = channel_order_agg['实收价格'].sum()
        else:
            total_sales = channel_order_agg['商品实售价'].sum()
        
        total_profit = channel_order_agg['订单实际利润'].sum()
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        print(f"   订单数: {total_orders:,}")
        print(f"   销售额: ¥{total_sales:,.2f}")
        print(f"   利润额: ¥{total_profit:,.2f}")
        print(f"   利润率: {profit_rate:.2f}%")
        
        drill_down_results.append({
            '渠道': channel_name,
            '订单数': total_orders,
            '销售额': total_sales,
            '利润额': total_profit,
            '利润率': profit_rate
        })
    
    # 5. 对比结果
    print(f"\n{'='*80}")
    print("🔍 数据一致性对比")
    print("="*80)
    
    drill_down_df = pd.DataFrame(drill_down_results)
    
    # 合并两个结果
    comparison = channel_stats.merge(
        drill_down_df,
        on='渠道',
        how='outer',
        suffixes=('_主看板', '_下钻')
    )
    
    # 计算差异
    comparison['订单数_差异'] = comparison['订单数_下钻'] - comparison['订单数_主看板']
    comparison['销售额_差异'] = comparison['销售额_下钻'] - comparison['销售额_主看板']
    comparison['利润额_差异'] = comparison['利润额_下钻'] - comparison['利润额_主看板']
    comparison['利润率_差异'] = comparison['利润率_下钻'] - comparison['利润率_主看板']
    
    print("\n📊 对比结果:")
    print(comparison.to_string(index=False))
    
    # 6. 判断是否一致
    print(f"\n{'='*80}")
    print("✅ 一致性检查")
    print("="*80)
    
    tolerance = 0.01  # 允许0.01的浮点误差
    
    all_consistent = True
    
    for _, row in comparison.iterrows():
        channel = row['渠道']
        
        # 检查订单数(必须完全一致)
        if abs(row['订单数_差异']) > 0:
            print(f"❌ {channel} - 订单数不一致: 主看板={row['订单数_主看板']}, 下钻={row['订单数_下钻']}")
            all_consistent = False
        
        # 检查销售额(允许小误差)
        if abs(row['销售额_差异']) > tolerance:
            print(f"❌ {channel} - 销售额不一致: 主看板=¥{row['销售额_主看板']:,.2f}, 下钻=¥{row['销售额_下钻']:,.2f}, 差异=¥{row['销售额_差异']:,.2f}")
            all_consistent = False
        
        # 检查利润额(允许小误差)
        if abs(row['利润额_差异']) > tolerance:
            print(f"❌ {channel} - 利润额不一致: 主看板=¥{row['利润额_主看板']:,.2f}, 下钻=¥{row['利润额_下钻']:,.2f}, 差异=¥{row['利润额_差异']:,.2f}")
            all_consistent = False
        
        # 检查利润率(允许小误差)
        if abs(row['利润率_差异']) > tolerance:
            print(f"❌ {channel} - 利润率不一致: 主看板={row['利润率_主看板']:.2f}%, 下钻={row['利润率_下钻']:.2f}%, 差异={row['利润率_差异']:.2f}%")
            all_consistent = False
    
    if all_consistent:
        print("✅ 所有渠道数据完全一致!")
    else:
        print("\n⚠️ 发现数据不一致,需要检查计算逻辑")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    test_data_consistency()
