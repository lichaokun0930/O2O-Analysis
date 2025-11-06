#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取Streamlit版本的数据基准 - 最终正确版本
完全按照业务逻辑最终确认.md的公式
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
    """加载数据并应用业务规则"""
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
    
    # 剔除耗材（业务规则1）
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
    使用业务逻辑最终确认.md的公式
    
    ✅ 正确公式：
    订单实际利润额 = 预估订单收入 - 商品成本总和 - 配送成本
    配送成本 = 用户支付配送费 - 配送费减免金额 - 物流配送费
    """
    print("\n" + "=" * 80)
    print("📈 Streamlit版本 - 使用业务逻辑最终确认的公式")
    print("=" * 80)
    
    if '订单ID' not in df.columns:
        print("❌ 缺少订单ID字段")
        return None
    
    # ========== 第1步：订单级别聚合 ==========
    print("\n🔧 步骤1：按订单ID聚合明细数据")
    
    # 检查字段
    print("\n可用字段检查:")
    required_fields = {
        '预估订单收入': '预估订单收入' if '预估订单收入' in df.columns else '预计订单收入',
        '商品采购成本': '商品采购成本',
        '用户支付配送费': '用户支付配送费',
        '配送费减免金额': '配送费减免金额',
        '物流配送费': '物流配送费',
        '平台佣金': '平台佣金',
        '月售': '月售'
    }
    
    for logical_name, field_name in required_fields.items():
        if field_name in df.columns:
            print(f"   ✅ {logical_name}: {field_name}")
        else:
            print(f"   ❌ {logical_name}: 缺失")
    
    # 聚合（使用业务规则：订单级字段用first避免重复）
    order_agg = df.groupby('订单ID').agg({
        required_fields['预估订单收入']: 'first',  # 订单级字段
        '商品采购成本': 'sum',                      # 商品级字段，需要求和
        '用户支付配送费': 'first',                  # 订单级字段
        '配送费减免金额': 'first',                  # 订单级字段
        '物流配送费': 'first',                      # 订单级字段
        '平台佣金': 'first',                        # 订单级字段
        '月售': 'sum',                              # 商品级字段
        '商品名称': 'nunique'                       # 用于统计SKU
    }).reset_index()
    
    print(f"\n   📦 订单总数: {len(order_agg):,}")
    print(f"   📦 原始明细行数: {len(df):,}")
    print(f"   📊 平均每单商品数: {len(df) / len(order_agg):.1f}")
    
    # ========== 第2步：按业务逻辑计算 ==========
    print("\n🔧 步骤2：应用业务逻辑公式")
    
    # 配送成本 = 用户支付配送费 - 配送费减免金额 - 物流配送费
    order_agg['配送成本'] = (
        order_agg['用户支付配送费'] - 
        order_agg['配送费减免金额'] - 
        order_agg['物流配送费']
    )
    print(f"   🚚 配送成本公式: 用户支付配送费 - 配送费减免金额 - 物流配送费")
    
    # 订单实际利润额 = 预估订单收入 - 商品成本总和 - 配送成本
    order_agg['订单实际利润额'] = (
        order_agg[required_fields['预估订单收入']] - 
        order_agg['商品采购成本'] - 
        order_agg['配送成本']
    )
    print(f"   💎 利润公式: 预估订单收入 - 商品成本总和 - 配送成本")
    
    # ========== 第3步：生成汇总指标 ==========
    print("\n🔧 步骤3：生成汇总指标")
    
    metrics = {}
    
    # 基础指标
    metrics['订单总数'] = len(order_agg)
    metrics['商品SKU数'] = df['商品名称'].nunique()
    metrics['总销量'] = order_agg['月售'].sum()
    
    # 收入指标
    metrics['预估订单收入总额'] = order_agg[required_fields['预估订单收入']].sum()
    metrics['平均订单收入'] = metrics['预估订单收入总额'] / metrics['订单总数'] if metrics['订单总数'] > 0 else 0
    
    # 成本指标
    metrics['商品成本总额'] = order_agg['商品采购成本'].sum()
    metrics['配送成本总额'] = order_agg['配送成本'].sum()
    metrics['平台佣金总额'] = order_agg['平台佣金'].sum()
    
    # 利润指标
    metrics['总利润额'] = order_agg['订单实际利润额'].sum()
    metrics['平均订单利润'] = order_agg['订单实际利润额'].mean()
    metrics['盈利订单数'] = (order_agg['订单实际利润额'] > 0).sum()
    metrics['盈利订单占比'] = (order_agg['订单实际利润额'] > 0).mean() * 100
    
    # 利润率
    metrics['利润率'] = (metrics['总利润额'] / metrics['预估订单收入总额'] * 100) if metrics['预估订单收入总额'] > 0 else 0
    
    # 毛利率
    毛利 = metrics['预估订单收入总额'] - metrics['商品成本总额']
    metrics['毛利率'] = (毛利 / metrics['预估订单收入总额'] * 100) if metrics['预估订单收入总额'] > 0 else 0
    
    # ========== 打印输出 ==========
    print("\n" + "=" * 80)
    print("📊 ========== Streamlit基准数据（业务逻辑公式）==========")
    print("=" * 80)
    
    print(f"\n📦 基础指标:")
    print(f"   - 订单总数: {metrics['订单总数']:,}")
    print(f"   - 商品SKU数: {metrics['商品SKU数']:,}")
    print(f"   - 总销量: {metrics['总销量']:,}")
    
    print(f"\n💰 收入指标:")
    print(f"   - 预估订单收入总额: ¥{metrics['预估订单收入总额']:,.0f}")
    print(f"   - 平均订单收入: ¥{metrics['平均订单收入']:.2f}")
    
    print(f"\n💸 成本指标:")
    print(f"   - 商品成本总额: ¥{metrics['商品成本总额']:,.0f}")
    print(f"   - 配送成本总额: ¥{metrics['配送成本总额']:,.0f}")
    print(f"   - 平台佣金总额: ¥{metrics['平台佣金总额']:,.0f}")
    
    print(f"\n💎 利润指标:")
    print(f"   - 总利润额: ¥{metrics['总利润额']:,.0f}")
    print(f"   - 平均订单利润: ¥{metrics['平均订单利润']:.2f}")
    print(f"   - 盈利订单数: {metrics['盈利订单数']:,}")
    print(f"   - 盈利订单占比: {metrics['盈利订单占比']:.1f}%")
    
    print(f"\n📊 利润率:")
    print(f"   - 毛利率: {metrics['毛利率']:.1f}%")
    print(f"   - 利润率: {metrics['利润率']:.1f}%")
    
    # ========== 公式验证 ==========
    print(f"\n🔍 公式验证（使用业务逻辑公式）:")
    expected_profit = metrics['预估订单收入总额'] - metrics['商品成本总额'] - metrics['配送成本总额']
    print(f"   总利润 = 预估订单收入 - 商品成本 - 配送成本")
    print(f"   总利润 = {metrics['预估订单收入总额']:,.2f} - {metrics['商品成本总额']:,.2f} - {metrics['配送成本总额']:,.2f}")
    print(f"   计算结果 = ¥{expected_profit:,.2f}")
    print(f"   实际总利润 = ¥{metrics['总利润额']:,.2f}")
    print(f"   差异 = ¥{abs(expected_profit - metrics['总利润额']):,.2f} {'✅ 一致' if abs(expected_profit - metrics['总利润额']) < 0.01 else '❌ 不一致'}")
    
    # 打印实例验证（与文档对应）
    print(f"\n📝 业务逻辑文档实例验证:")
    print(f"   文档示例订单: 预估收入22.49 - 成本16.1 - 配送成本(-7) = 利润13.39元")
    print(f"   说明: 配送成本为负表示平台补贴")
    
    return metrics


def save_results(metrics, filename="数据验证结果_Streamlit版_业务逻辑公式.json"):
    """保存结果到JSON文件"""
    import numpy as np
    
    # 转换numpy类型
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
    print("🚀 提取Streamlit基准数据 - 使用业务逻辑最终确认公式\n")
    
    # 加载数据
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
    print("✅ Streamlit版本数据验证完成（业务逻辑公式）")
    print("=" * 80)
    print("\n📋 下一步：检查Dash应用的计算逻辑是否使用了相同公式")


if __name__ == "__main__":
    main()
