#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取Streamlit版本的数据基准 - 正确版本
完全按照Streamlit的计算逻辑（订单级别聚合）
"""

import pandas as pd
import sys
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

# 导入真实数据处理器
sys.path.insert(0, str(APP_DIR))
from 真实数据处理器 import RealDataProcessor

def load_and_standardize_data():
    """加载数据并应用Streamlit的业务规则"""
    print("=" * 80)
    print("📂 加载数据并标准化")
    print("=" * 80)
    
    # 加载Excel文件
    excel_file = APP_DIR / "门店数据" / "2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
    
    if not excel_file.exists():
        print(f"❌ 文件不存在: {excel_file}")
        return None
    
    print(f"📄 读取文件: {excel_file.name}")
    df = pd.read_excel(excel_file)
    print(f"📊 原始数据加载: {len(df):,} 行 × {len(df.columns)} 列")
    
    # 使用RealDataProcessor标准化
    processor = RealDataProcessor("实际数据")
    df_standardized = processor.standardize_sales_data(df)
    print(f"✅ 数据标准化完成: {len(df_standardized):,} 行")
    
    # 剔除耗材
    if '一级分类名' in df_standardized.columns:
        before_count = len(df_standardized)
        df_standardized = df_standardized[df_standardized['一级分类名'] != '耗材'].copy()
        removed_material = before_count - len(df_standardized)
        print(f"🔴 已剔除耗材数据: {removed_material:,} 行")
        print(f"📊 剔除耗材后数据量: {len(df_standardized):,} 行")
    
    # 剔除咖啡渠道
    if '渠道' in df_standardized.columns:
        exclude_channels = ['饿了么咖啡', '美团咖啡']
        before_count = len(df_standardized)
        df_standardized = df_standardized[~df_standardized['渠道'].isin(exclude_channels)].copy()
        removed_coffee = before_count - len(df_standardized)
        print(f"☕ 已剔除咖啡渠道数据: {removed_coffee:,} 行")
        print(f"📊 最终数据量: {len(df_standardized):,} 行")
    
    return df_standardized


def calculate_streamlit_metrics(df):
    """
    完全按照Streamlit版本的计算逻辑（订单级别聚合）
    参考：智能门店经营看板_可视化.py 的 calculate_order_metrics 函数
    """
    print("\n" + "=" * 80)
    print("📈 Streamlit版本 - 订单级别指标计算")
    print("=" * 80)
    
    if '订单ID' not in df.columns:
        print("❌ 缺少订单ID字段，无法进行订单级别聚合")
        return None
    
    # ========== 第1步：创建订单级别聚合 ==========
    print("\n🔧 步骤1：按订单ID聚合明细数据")
    
    order_agg = df.groupby('订单ID').agg({
        '商品实售价': 'sum',           # 商品销售额（订单内所有商品）
        '商品原价': 'sum',             # 商品原价总额
        '商品采购成本': 'sum',         # 商品成本
        '月售': 'sum',                 # 数量
        '物流配送费': 'first',         # 订单级字段（每个订单只有一个值）
        '平台佣金': 'first',
        '打包袋金额': 'first',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first'
    }).reset_index()
    
    print(f"   📦 订单总数: {len(order_agg):,}")
    print(f"   📦 原始明细行数: {len(df):,}")
    print(f"   📊 平均每单商品数: {len(df) / len(order_agg):.1f}")
    
    # ========== 第2步：计算订单级别的收入和成本 ==========
    print("\n🔧 步骤2：计算订单级别的收入和成本")
    
    # 订单总收入 = 商品实售价 + 打包费 + 用户支付配送费
    # 这是Streamlit中显示的"订单总收入"
    order_agg['订单总收入'] = (
        order_agg['商品实售价'] + 
        order_agg['打包袋金额'] + 
        order_agg['用户支付配送费']
    )
    print(f"   💰 订单总收入公式: 商品实售价 + 打包费 + 用户支付配送费")
    
    # 配送净成本 = (配送费减免 + 物流配送费) - 用户支付配送费
    # Streamlit中显示的"总配送成本"
    order_agg['配送成本'] = (
        order_agg['配送费减免金额'] + 
        order_agg['物流配送费'] - 
        order_agg['用户支付配送费']
    )
    print(f"   🚚 配送成本公式: (配送费减免 + 物流配送费) - 用户支付配送费")
    
    # 活动营销成本 = 满减 + 商家代金券
    order_agg['活动营销成本'] = (
        order_agg['满减金额'] + 
        order_agg['商家代金券']
    )
    print(f"   🎯 活动营销成本公式: 满减金额 + 商家代金券")
    
    # 商品折扣成本 = 商品原价 - 商品实售价
    # Streamlit中显示的"商品折扣成本"
    order_agg['商品折扣成本'] = (
        order_agg['商品原价'] - 
        order_agg['商品实售价']
    )
    print(f"   💸 商品折扣成本公式: 商品原价 - 商品实售价")
    
    # 订单实际利润 = 订单总收入 - 成本 - 配送成本 - 活动营销成本 - 商品折扣成本 - 平台佣金
    order_agg['订单实际利润'] = (
        order_agg['订单总收入'] - 
        order_agg['商品采购成本'] - 
        order_agg['配送成本'] - 
        order_agg['活动营销成本'] - 
        order_agg['商品折扣成本'] - 
        order_agg['平台佣金']
    )
    print(f"   💎 总利润公式: 订单总收入 - 商品采购成本 - 配送成本 - 活动营销成本 - 商品折扣成本 - 平台佣金")
    
    # ========== 第3步：生成汇总指标 ==========
    print("\n🔧 步骤3：生成汇总指标")
    
    metrics = {}
    
    # ===== 基础指标 =====
    metrics['订单总数'] = len(order_agg)
    metrics['商品SKU数'] = df['商品名称'].nunique()
    metrics['总销量'] = order_agg['月售'].sum()
    
    # ===== 收入指标 =====
    metrics['商品销售额'] = order_agg['商品实售价'].sum()
    metrics['订单总收入'] = order_agg['订单总收入'].sum()
    metrics['平均客单价'] = metrics['商品销售额'] / metrics['订单总数'] if metrics['订单总数'] > 0 else 0
    
    # ===== 成本指标 =====
    metrics['总商品成本'] = order_agg['商品采购成本'].sum()
    metrics['总配送成本'] = order_agg['配送成本'].sum()
    metrics['活动营销成本'] = order_agg['活动营销成本'].sum()
    metrics['商品折扣成本'] = order_agg['商品折扣成本'].sum()
    metrics['平台佣金'] = order_agg['平台佣金'].sum()
    
    # ===== 利润指标 =====
    metrics['总利润额'] = order_agg['订单实际利润'].sum()
    metrics['平均订单利润'] = order_agg['订单实际利润'].mean()
    
    # 盈利订单分析
    metrics['盈利订单数'] = (order_agg['订单实际利润'] > 0).sum()
    metrics['盈利订单占比'] = (order_agg['订单实际利润'] > 0).mean() * 100
    
    # 利润率
    metrics['整体利润率'] = (metrics['总利润额'] / metrics['商品销售额'] * 100) if metrics['商品销售额'] > 0 else 0
    
    # 毛利率
    单品毛利 = metrics['商品销售额'] - metrics['总商品成本']
    metrics['毛利率'] = (单品毛利 / metrics['商品销售额'] * 100) if metrics['商品销售额'] > 0 else 0
    
    # ========== 打印输出（与Streamlit截图对应）==========
    print("\n" + "=" * 80)
    print("📊 ========== Streamlit基准数据（与截图对应）==========")
    print("=" * 80)
    
    print(f"\n📦 基础指标:")
    print(f"   - 订单总数: {metrics['订单总数']:,}")
    print(f"   - 商品SKU数: {metrics['商品SKU数']:,}")
    print(f"   - 总销量: {metrics['总销量']:,}")
    
    print(f"\n💰 收入指标:")
    print(f"   - 商品销售额: ¥{metrics['商品销售额']:,.0f}")
    print(f"   - 订单总收入: ¥{metrics['订单总收入']:,.0f}")
    print(f"   - 平均客单价: ¥{metrics['平均客单价']:.2f}")
    
    print(f"\n💸 成本结构分析:")
    print(f"   - 总商品成本: ¥{metrics['总商品成本']:,.0f}")
    print(f"   - 总配送成本: ¥{metrics['总配送成本']:,.0f}")
    print(f"   - 活动营销成本: ¥{metrics['活动营销成本']:,.0f}")
    print(f"   - 商品折扣成本: ¥{metrics['商品折扣成本']:,.0f}")
    print(f"   - 平台佣金: ¥{metrics['平台佣金']:,.0f}")
    
    print(f"\n💎 利润深度分析:")
    print(f"   - 总利润额: ¥{metrics['总利润额']:,.0f}")
    print(f"   - 平均订单利润: ¥{metrics['平均订单利润']:,.2f}")
    print(f"   - 盈利订单数: {metrics['盈利订单数']:,}")
    print(f"   - 盈利订单占比: {metrics['盈利订单占比']:.1f}%")
    
    print(f"\n📊 利润率分析:")
    print(f"   - 毛利率: {metrics['毛利率']:.1f}%")
    print(f"   - 整体利润率: {metrics['整体利润率']:.1f}%")
    
    # ========== 公式验证 ==========
    print(f"\n🔍 公式验证:")
    expected_profit = (
        metrics['订单总收入'] - 
        metrics['总商品成本'] - 
        metrics['总配送成本'] - 
        metrics['活动营销成本'] - 
        metrics['商品折扣成本'] - 
        metrics['平台佣金']
    )
    print(f"   总利润 = 订单总收入 - 商品成本 - 配送成本 - 活动营销 - 商品折扣 - 平台佣金")
    print(f"   总利润 = {metrics['订单总收入']:,.2f} - {metrics['总商品成本']:,.2f} - {metrics['总配送成本']:,.2f} - {metrics['活动营销成本']:,.2f} - {metrics['商品折扣成本']:,.2f} - {metrics['平台佣金']:,.2f}")
    print(f"   计算结果 = ¥{expected_profit:,.2f}")
    print(f"   实际总利润 = ¥{metrics['总利润额']:,.2f}")
    print(f"   差异 = ¥{abs(expected_profit - metrics['总利润额']):,.2f} {'✅ 一致' if abs(expected_profit - metrics['总利润额']) < 0.01 else '❌ 不一致'}")
    
    return metrics


def save_results(metrics, filename="数据验证结果_Streamlit版_正确.json"):
    """保存结果到JSON文件"""
    import numpy as np
    
    # 转换numpy类型为Python原生类型
    metrics_serializable = {}
    for k, v in metrics.items():
        if isinstance(v, (np.integer, np.int64, np.int32)):
            metrics_serializable[k] = int(v)
        elif isinstance(v, (np.floating, np.float64, np.float32)):
            metrics_serializable[k] = float(v)
        else:
            metrics_serializable[k] = v
    
    output_file = APP_DIR / filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics_serializable, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_file}")
    return str(output_file)


def main():
    """主函数"""
    print("🚀 开始提取Streamlit版本的数据基准（正确版本）\n")
    
    # 加载并标准化数据
    df = load_and_standardize_data()
    if df is None:
        return
    
    # 计算指标
    metrics = calculate_streamlit_metrics(df)
    if metrics is None:
        return
    
    # 保存结果
    save_results(metrics)
    
    print("\n" + "=" * 80)
    print("✅ Streamlit版本数据验证完成（正确版本）")
    print("=" * 80)
    print("\n📋 下一步：在Dash应用中上传相同数据，对比13个关键指标")
    print("   1. 打开 http://localhost:8050")
    print("   2. 上传: 门店数据/2025-09-01至2025-09-30订单明细数据导出汇总 (2).xlsx")
    print("   3. 查看Tab 1的指标卡片")
    print("   4. 对比差异并回报")


if __name__ == "__main__":
    main()
